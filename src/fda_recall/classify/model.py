"""TF-IDF + logistic regression root-cause classifier vs keyword baseline (T3.2.2).

    python -m fda_recall.classify.model

Configuration fixed a priori (not tuned on the gold set): word 1-2-gram + char_wb 3-5-gram TF-IDF
(sublinear tf), LogisticRegression(C=10, class_weight='balanced'). Out-of-fold predictions from
GroupKFold(5) grouped by normalized recalling firm (prevents near-duplicate leakage). The keyword baseline
is scored on the same rows. Paired bootstrap (2,000 resamples, seed 42) for the macro-F1 difference;
McNemar exact test on per-row correctness.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.sparse import hstack  # noqa: E402,F401
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, f1_score  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402
from sklearn.pipeline import FeatureUnion, make_pipeline  # noqa: E402
from statsmodels.stats.contingency_tables import mcnemar  # noqa: E402

from ..metrics import record_metric  # noqa: E402
from .rules import RuleClassifier, normalize  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "labels" / "gold_v1.csv"
EVENTS = ROOT / "data" / "processed" / "recalls_event.parquet"
REPORT = ROOT / "reports" / "classifier_eval.md"
FIG = ROOT / "reports" / "figures" / "confusion_matrix.png"
OOF_OUT = ROOT / "data" / "interim" / "gold_oof_predictions.csv"
SEED = 42


def build_model() -> object:
    feats = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1)),
    ])
    return make_pipeline(feats, LogisticRegression(C=10, class_weight="balanced", max_iter=5000,
                                                   random_state=SEED))


def oof_predict(texts: pd.Series, y: pd.Series, groups: pd.Series, n_splits: int = 5):
    pred = pd.Series(index=texts.index, dtype=object)
    conf = pd.Series(index=texts.index, dtype=float)
    for tr, te in GroupKFold(n_splits=n_splits).split(texts, y, groups):
        m = build_model().fit(texts.iloc[tr], y.iloc[tr])
        proba = m.predict_proba(texts.iloc[te])
        pred.iloc[te] = m.classes_[proba.argmax(1)]
        conf.iloc[te] = proba.max(1)
    return pred, conf


def macro_f1(y, p, labels) -> float:
    return f1_score(y, p, labels=labels, average="macro", zero_division=0)


def paired_bootstrap(y, p_ml, p_base, labels, n: int = 2000, seed: int = SEED):
    rng = np.random.default_rng(seed)
    y, p_ml, p_base = map(np.asarray, (y, p_ml, p_base))
    ml, base, diff = [], [], []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        a, b = macro_f1(y[i], p_ml[i], labels), macro_f1(y[i], p_base[i], labels)
        ml.append(a)
        base.append(b)
        diff.append(a - b)
    ci = lambda v: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))  # noqa: E731
    return {"ml_ci": ci(ml), "base_ci": ci(base), "diff_ci": ci(diff)}


def mcnemar_p(y, p_ml, p_base) -> tuple[float, list[list[int]]]:
    a, b = np.asarray(p_ml) == np.asarray(y), np.asarray(p_base) == np.asarray(y)
    table = [[int((a & b).sum()), int((a & ~b).sum())], [int((~a & b).sum()), int((~a & ~b).sum())]]
    return float(mcnemar(table, exact=True).pvalue), table


def load_gold() -> pd.DataFrame:
    gold = pd.read_csv(GOLD, dtype=str, keep_default_na=False)
    ev = pd.read_parquet(EVENTS, columns=["event_id", "firm_norm"])
    gold = gold.merge(ev, on="event_id", how="left", validate="one_to_one")
    assert gold.firm_norm.notna().all()
    gold["text"] = gold.reason_text.map(normalize)
    return gold


def main() -> int:
    gold = load_gold()
    labels = sorted(gold.label.unique())
    pred, conf = oof_predict(gold.text, gold.label, gold.firm_norm)
    base = pd.Series(RuleClassifier().predict(gold.reason_text), index=gold.index)
    gold["oof_pred"], gold["oof_conf"], gold["rule_pred"] = pred, conf, base
    OOF_OUT.parent.mkdir(parents=True, exist_ok=True)
    gold[["event_id", "source", "label", "oof_pred", "oof_conf", "rule_pred"]].to_csv(OOF_OUT, index=False)

    L = ["", "## TF-IDF + logistic regression (T3.2.2)", "",
         "Config fixed a priori (see module docstring). GroupKFold(5) by normalized firm; out-of-fold (OOF) "
         "predictions compared with the keyword baseline on identical rows. 95% CIs: paired bootstrap, 2,000 "
         "resamples, seed 42. McNemar exact test on per-row correctness.", ""]
    src = "classify/model.py"
    for name, mask in [("all", gold.index == gold.index), ("random", gold.source == "random")]:
        y, pm, pb = gold.label[mask], gold.oof_pred[mask], gold.rule_pred[mask]
        f_ml, f_b = macro_f1(y, pm, labels), macro_f1(y, pb, labels)
        bs = paired_bootstrap(y, pm, pb, labels)
        p, table = mcnemar_p(y, pm, pb)
        L += [f"### Subset: {name} (n={int(mask.sum())})", "",
              "| model | macro-F1 | 95% CI | accuracy |", "|---|---|---|---|",
              f"| TF-IDF + LR (OOF) | {f_ml:.3f} | {bs['ml_ci'][0]:.3f}-{bs['ml_ci'][1]:.3f} | {(y == pm).mean():.3f} |",
              f"| Keyword baseline | {f_b:.3f} | {bs['base_ci'][0]:.3f}-{bs['base_ci'][1]:.3f} | {(y == pb).mean():.3f} |",
              "",
              f"Difference (ML - baseline): {f_ml - f_b:+.3f}, 95% CI {bs['diff_ci'][0]:+.3f} to {bs['diff_ci'][1]:+.3f}. "
              f"McNemar exact p = {p:.3f} (table both-right/ML-only/base-only/both-wrong = "
              f"{table[0][0]}/{table[0][1]}/{table[1][0]}/{table[1][1]}).", "",
              "Target (charter M2/M3, NOT a result): ML macro-F1 >= 0.80 and uplift >= +0.10 with CI excluding 0. "
              f"Met: macro-F1 {'yes' if f_ml >= 0.80 else 'no'}; uplift {'yes' if (f_ml - f_b >= 0.10 and bs['diff_ci'][0] > 0) else 'no'}.",
              ""]
        record_metric(f"clf.ml_macro_f1_{name}", round(f_ml, 4), src)
        record_metric(f"clf.ml_macro_f1_ci_{name}", [round(x, 4) for x in bs["ml_ci"]], src)
        record_metric(f"clf.uplift_vs_rules_{name}", round(f_ml - f_b, 4), src)
        record_metric(f"clf.uplift_ci_{name}", [round(x, 4) for x in bs["diff_ci"]], src)
        record_metric(f"clf.mcnemar_p_{name}", round(p, 4), src)
    L += ["### Per-class report (TF-IDF + LR, OOF, all 300)", "", "```",
          classification_report(gold.label, gold.oof_pred, labels=labels, zero_division=0), "```", ""]
    fig, ax = plt.subplots(figsize=(10, 9))
    ConfusionMatrixDisplay.from_predictions(gold.label, gold.oof_pred, labels=labels, ax=ax,
                                            xticks_rotation=60, colorbar=False)
    ax.set_title("TF-IDF + LR out-of-fold confusion matrix (gold set, n=300)")
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG, dpi=120)
    plt.close(fig)
    text = REPORT.read_text(encoding="utf-8").split("\n## TF-IDF")[0]
    REPORT.write_text(text.rstrip() + "\n" + "\n".join(L), encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
