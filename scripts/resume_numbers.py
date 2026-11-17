"""Print every number used in the resume bullets / pitch with its metrics.json key and label (T7.1.3).

    python scripts/resume_numbers.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "results" / "metrics.json"
KEYS = [  # (where used, key)
    ("bullet 1", "clf.corpus_n_events"), ("bullet 1", "clf.rules_macro_f1_all"), ("bullet 1", "clf.ml_macro_f1_all"),
    ("bullet 1", "clf.uplift_ci_all"), ("bullet 1", "clf.corpus_coverage"), ("bullet 1", "clf.prod_precision_accepted_all"),
    ("bullet 1", "labels.n_gold"), ("bullet 1", "labels.kappa_llm_a_vs_b"),
    ("bullet 2", "series.n_months"), ("bullet 2", "pareto.drugs.vital_few_k"), ("bullet 2", "pareto.food.vital_few_k"),
    ("bullet 2", "pareto.drugs.vital_few_share"), ("bullet 2", "pareto.food.vital_few_share"),
    ("bullet 2", "spc.sim_lambda1.r1_per_point"), ("bullet 2", "spc.n_categories"),
    ("bullet 3", "backtest.n_origins"), ("bullet 3", "backtest.target_met"), ("bullet 3", "backtest.momentum_rho"),
    ("bullet 3", "backtest.p_at_3"), ("bullet 3", "backtest.best_baseline_p_at_3"),
    ("pitch", "data.n_events"), ("Q&A", "backtest.n_cells"), ("Q&A", "backtest.spearman_rho"),
    ("Q&A", "sens.median_tau_weights"), ("Q&A", "trend.n_significant_q05"),
]


def main() -> int:
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    missing = 0
    print(f"{'used in':9} {'key':40} {'value':>14}  label")
    for where, k in KEYS:
        if k not in m:
            print(f"{where:9} {k:40} {'MISSING':>14}")
            missing += 1
            continue
        v = m[k]
        print(f"{where:9} {k:40} {str(v['value']):>14}  {v.get('label', '?')}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
