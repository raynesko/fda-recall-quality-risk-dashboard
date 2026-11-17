# 5. Validation & Metrics Plan

All thresholds below are **targets**. Achieved values are recorded only through `record_metric` into `results/metrics.json`; the resume may use only those.

## A. Root-cause classifier (SE3)
- **Ground truth:** 300-event gold set (200 random stratified by product_type x year, 100 targeted for rare classes). Not prevalence-representative -> used for accuracy only, never for category shares.
- **Label quality:** independent second LLM annotator relabels 60 events blind; Cohen's kappa (target >= 0.75). LLM annotators (A labels all; independent B relabels 60) -> agreement reported as LLM inter-annotator kappa, not human.
- **Baseline definition:** ordered keyword/regex rules written from taxonomy + EDA only (what an analyst could build in Excel). Frozen before first gold evaluation.
- **Candidate:** TF-IDF + logistic regression (balanced class weights). **CV:** GroupKFold(5) grouped by normalized recalling firm (prevents near-duplicate leakage).
- **Metrics:** macro-F1 (primary, because classes are imbalanced), per-class P/R/F1, accuracy, coverage.
- **Comparison:** both models on the same out-of-fold rows; paired bootstrap (>= 1,000 resamples) for macro-F1 difference with 95% CI; McNemar test on accuracy.
- **Operating point:** confidence threshold chosen on OOF predictions for >= 0.90 precision; below-threshold -> `Unclassified`. Report coverage at that threshold.
- **Targets:** macro-F1 >= 0.80; uplift >= +0.10 with CI excluding 0.

## B. SPC (SE4)
- **Correctness:** unit tests vs hand calculation (1e-9). 
- **False-alarm calibration:** simulate 1,000 stable Poisson series (n=60); report empirical false-alarm rate per rule (Poisson with small means departs from the 0.27% normal-theory value - that is why we simulate).
- **Chart choice:** c-chart (counts) and p-chart (category share of monthly events), Laney adjustment if dispersion > 1. Phase I 2015-01..2019-12 (configurable); sensitivity to 3 alternative baseline windows.
- **Trend tests:** Poisson (or NB if dispersion > 1.5) GLM, annual rate ratio with 95% CI, Benjamini-Hochberg q-values.

## C. Risk score backtest (SE5)
- **Pre-registration:** definition, weights, flag rule and success criteria committed in T5.1.1 before T5.1.2 runs.
- **Design:** rolling origins (6-monthly descriptive; 12-month-spaced for inference). Score uses only data <= origin (leakage test). Unit = category x product_type. Outcome = next-12-month log change in events (and Class I share as secondary).
- **Baselines:** B1 trailing-12m volume rank; B2 momentum-only; B3 random (permutation, 1,000 draws). Regression to the mean makes B2 important.
- **Metrics:** Spearman rho with block-bootstrap 95% CI; precision@3 with permutation p-value; lift vs best baseline.
- **Target:** precision@3 >= best baseline + 0.15 and rho CI excludes 0. Small n is stated beside each statistic. A miss is reported as a miss; resume framing then shifts from "predictive" to "monitoring framework with honest backtest".
- **Sensitivity:** 1,000 Dirichlet weight draws (median Kendall tau target >= 0.70; per-category flag stability %), window 6/12/24 m, label-noise injection at the classifier's measured error rate.

## D. Dashboard reconciliation (SE6)
Every KPI/chart total is reconciled to Python outputs in `docs/dashboard/reconciliation.md` (>= 5 values, zero difference). Usability: 2 reviewers x 5 tasks (target >= 4/5 unaided).

## E. Numbers permitted on the resume (placeholders until achieved; each maps to a metrics.json key)
| Resume figure | metrics.json key (planned) | Used only if |
|---|---|---|
| N recall events analyzed (drug + food) and date span | `data.n_events`, `data.date_min/max` | always (descriptive) |
| N LLM-annotated events; kappa | `labels.n_gold`, `labels.kappa` | kappa reported as achieved |
| Classifier macro-F1 and uplift vs keyword baseline with CI | `clf.macro_f1`, `clf.uplift_vs_rules`, `clf.uplift_ci` | achieved, whatever value |
| Share of recall events in top-k "vital few" categories | `pareto.vital_few_share` | descriptive |
| Control-chart signals detected / categories monitored | `spc.n_signals`, `spc.n_categories` | descriptive |
| Backtest precision@3 vs baseline | `backtest.p_at_3`, `backtest.best_baseline_p_at_3` | only if beating baseline; else state "evaluated against 3 baselines" without a lift claim |

Rule: do not write "predicts", "reduces recalls", or any improvement/savings claim. This project measures and monitors; it does not intervene.
