"""Evaluate the keyword baseline on the gold set (T3.2.1, criterion 3). Run once gold_v1.csv is labeled.

    python -m fda_recall.classify.evaluate_rules

Writes the baseline section of reports/classifier_eval.md and records metrics. The rules file sha256 is
recorded so any later edit to the rules is detectable (no git repo yet; switch to commit hash once added).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, f1_score

from ..metrics import record_metric
from .rules import RULES, RuleClassifier

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "labels" / "gold_v1.csv"
REPORT = ROOT / "reports" / "classifier_eval.md"


def evaluate(gold: pd.DataFrame) -> dict:
    pred = RuleClassifier().predict(gold.reason_text)
    labels = sorted(set(gold.label))
    out = {}
    for name, mask in [("all", gold.index == gold.index), ("random", gold.source == "random")]:
        y, p = gold.label[mask], pd.Series(pred, index=gold.index)[mask]
        out[name] = {"n": int(mask.sum()),
                     "macro_f1": f1_score(y, p, labels=labels, average="macro", zero_division=0),
                     "accuracy": float((y == p).mean()),
                     "coverage": float((p != "OTHER").mean()),
                     "report": classification_report(y, p, labels=labels, zero_division=0)}
    return out


def main() -> int:
    gold = pd.read_csv(GOLD, dtype=str, keep_default_na=False)
    if (gold.label == "").any():
        print(f"{int((gold.label == '').sum())} gold rows unlabeled - finish labeling first.")
        return 1
    res = evaluate(gold)
    sha = hashlib.sha256(RULES.read_bytes()).hexdigest()
    L = ["# Classifier Evaluation", "", "## Keyword baseline (T3.2.1)", "",
         f"Rules file `data/reference/keyword_rules.yaml` sha256 `{sha}` (frozen at first evaluation).", ""]
    for k, r in res.items():
        L += [f"### Subset: {k} (n={r['n']})", "",
              f"macro-F1 {r['macro_f1']:.3f} | accuracy {r['accuracy']:.3f} | coverage (not OTHER) {r['coverage']:.3f}",
              "", "```", r["report"], "```", ""]
        src = "classify/evaluate_rules.py"
        record_metric(f"clf.rules_macro_f1_{k}", round(r["macro_f1"], 4), src)
        record_metric(f"clf.rules_coverage_{k}", round(r["coverage"], 4), src)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:8]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
