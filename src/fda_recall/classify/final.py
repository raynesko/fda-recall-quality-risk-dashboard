"""Classify the full corpus (T3.2.4).

    python -m fda_recall.classify.final

Production classifier = frozen keyword rules (data/reference/keyword_rules.yaml). Decision 2026-11-16:
the TF-IDF + LR model lost to the rules on the gold set (reports/classifier_eval.md), so it is kept only
as a documented comparison (columns ml_category / ml_confidence, artifact models/classifier.joblib).

Policy
- No rule match -> category UNCLASSIFIED, method "unclassified". Never forced into OTHER: on the gold set
  rule-predicted OTHER had precision 0.13, i.e. "no match" means "unknown", not "other cause".
- confidence = empirical precision on the gold set of the event's match bucket (1 rule matched vs >= 2
  rules matched, tie broken by taxonomy priority). The rules were frozen before gold evaluation, so gold
  precision is an out-of-sample estimate (caveat: rules and gold labels share an author).
- Operating point: accept every rule match (primary). Single-match-only is computed as a sensitivity
  alternative and recorded; it is NOT used downstream unless stated.
"""
from __future__ import annotations

import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from ..metrics import record_metric
from .model import build_model
from .rules import RuleClassifier

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "labels" / "gold_v1.csv"
EVENTS = ROOT / "data" / "processed" / "recalls_event.parquet"
OUT = ROOT / "data" / "processed" / "events_classified.parquet"
MODEL_OUT = ROOT / "models" / "classifier.joblib"
GOLD_SCORED = ROOT / "data" / "interim" / "gold_rule_scored.csv"
SRC = "classify/final.py"
SEED = 42
UNCLASSIFIED = "UNCLASSIFIED"


def bucket(n_matches: int) -> str:
    return "none" if n_matches == 0 else ("single" if n_matches == 1 else "multi")


def apply_rules(texts: pd.Series, rc: RuleClassifier) -> pd.DataFrame:
    m = texts.map(rc.matches)
    out = pd.DataFrame({"rule_matches": m.map("|".join), "n_rule_matches": m.map(len)}, index=texts.index)
    out["category"] = m.map(lambda x: x[0] if x else UNCLASSIFIED)
    out["method"] = np.where(out["n_rule_matches"] > 0, "rules", "unclassified")
    out["match_bucket"] = out["n_rule_matches"].map(bucket)
    return out


def precision_ci(ok: np.ndarray, n: int = 2000, seed: int = SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    s = [ok[rng.integers(0, len(ok), len(ok))].mean() for _ in range(n)]
    return float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def main() -> int:
    rc = RuleClassifier()
    gold = pd.read_csv(GOLD, dtype={"event_id": str})
    ev = pd.read_parquet(EVENTS)

    # --- operating point on the gold set -------------------------------------------------------
    g = pd.concat([gold, apply_rules(gold["reason_text"], rc)], axis=1)
    g["ok"] = g["category"] == g["label"]
    bucket_prec = g[g.n_rule_matches > 0].groupby("match_bucket")["ok"].mean().to_dict()
    GOLD_SCORED.parent.mkdir(parents=True, exist_ok=True)
    g.to_csv(GOLD_SCORED, index=False)

    for subset, d in (("all", g), ("random", g[g.source == "random"])):
        acc = d[d.n_rule_matches > 0]
        lo, hi = precision_ci(acc["ok"].to_numpy())
        record_metric(f"clf.prod_precision_accepted_{subset}", round(acc["ok"].mean(), 3), SRC,
                      note=f"rules, accept any match; n_accepted={len(acc)}/{len(d)}; 95% bootstrap CI {lo:.3f}-{hi:.3f}")
        record_metric(f"clf.prod_coverage_gold_{subset}", round(len(acc) / len(d), 3), SRC)
        single = d[d.n_rule_matches == 1]
        record_metric(f"clf.alt_single_match_precision_{subset}", round(single["ok"].mean(), 3), SRC,
                      note=f"sensitivity operating point; coverage {len(single) / len(d):.3f}")
    record_metric("clf.production_method", "keyword_rules_v1", SRC,
                  note="ML (TF-IDF+LR) lost to rules on gold set; kept as comparison only")

    # --- full corpus ------------------------------------------------------------------------------
    r = apply_rules(ev["reason_for_recall"], rc)
    r["confidence"] = r["match_bucket"].map(bucket_prec).astype(float)  # NaN for unclassified

    model = build_model().fit(gold["reason_text"], gold["label"])
    proba = model.predict_proba(ev["reason_for_recall"].fillna(""))
    r["ml_category"] = model.classes_[proba.argmax(1)]
    r["ml_confidence"] = proba.max(1)

    out = pd.concat([ev[["event_id", "product_type", "report_month", "classification", "class_severity"]], r],
                    axis=1)
    out["is_gold"] = out["event_id"].isin(set(gold["event_id"]))
    assert len(out) == len(ev) and out["event_id"].is_unique, "row count must equal event table"
    assert out["category"].notna().all() and out["method"].isin(["rules", "unclassified"]).all()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "role": "comparison only (not production)", "trained_on": str(GOLD.name),
                 "n_train": len(gold), "sklearn_version": sklearn.__version__,
                 "python_version": platform.python_version()}, MODEL_OUT)

    acc = out[out.method == "rules"]
    record_metric("clf.corpus_n_events", len(out), SRC)
    record_metric("clf.corpus_coverage", round(len(acc) / len(out), 3), SRC,
                  note="share of events with >= 1 rule match")
    record_metric("clf.corpus_unclassified_share", round(1 - len(acc) / len(out), 3), SRC)
    record_metric("clf.corpus_multi_match_share", round((out.match_bucket == "multi").mean(), 3), SRC)
    record_metric("clf.corpus_rules_ml_agreement", round((acc.category == acc.ml_category).mean(), 3), SRC,
                  note="agreement between production rules and comparison ML on rule-accepted events")
    print(out["category"].value_counts().to_string())
    print({"coverage": len(acc) / len(out), "bucket_precision": bucket_prec})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
