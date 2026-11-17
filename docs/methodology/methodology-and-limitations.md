# Methodology and Limitations (T7.1.2)

This document is the single honest account of what was done, what worked and what did not. Every number is followed by its `results/metrics.json` key, which is listed again in the trace table at the end. Numbers that are not in that file do not appear here.

## 1. Data lineage
1. **Source:** openFDA drug and food enforcement endpoints, bulk download (`src/fda_recall/ingest.py`).
   - Files are kept immutable in `data/raw/<endpoint>/<date>/`, with a `manifest.json` recording URL, row count and SHA-256.
2. **Cleaning** (`clean.py`):
   - Dates are parsed; invalid values are listed in `reports/data_quality.md`.
   - Firm names are normalized.
   - Blank recall numbers get synthetic keys and are flagged.
   - Output: **47,708 product rows** (`data.n_product_rows`), collapsed to **12,687 recall events** (`data.n_events`).
   - Event rule: the most common reason text, the most severe class and the earliest dates.
   - Report dates run from 2012-06-20 to 2026-11-04 (`data.report_date_min`, `data.report_date_max`).
3. **Star schema** (`model.py`) for Power BI: fact_recall_event, fact_recall_product, dim_date, dim_firm and dim_category. Row counts and foreign keys are tested.
4. **Monthly series** (`analysis/series.py`):
   - Month = `report_date` month.
   - The first partial month (2012-06) and the latest partial month are excluded, leaving 172 months (`series.n_months`) from 2012-07 (`series.month_start`) to 2026-10 (`series.month_end`), with 12,609 events (`series.n_events_in_window`).
   - Sensitivity series: initiation-date months, with the last 6 months truncated (`series.initiation_truncation_months`, derived from the report-lag P90 of 160 days, `data.lag_p90_days`).

## 2. Root-cause classification
- **Taxonomy:** 14 categories describing the *stated* reason for recall (`data/reference/taxonomy.yaml`, tie-break priority, change log).
- **Gold set:** 300 events (`labels.n_gold`): 200 random, stratified by product type × year, plus 100 targeted at rare categories.
  - All 300 were labeled by an LLM annotator (A).
  - A second, independent LLM annotator (B) relabeled 60 blind. Kappa = 0.981 (`labels.kappa_llm_a_vs_b`); treat this as an upper bound (limitation L3).
- **Compared models:**
  - A frozen keyword/regex baseline.
  - TF-IDF + logistic regression, with configuration fixed a priori and 5-fold cross-validation grouped by firm (out-of-fold predictions).
- **Comparison result:** the rules scored macro-F1 0.802 (`clf.rules_macro_f1_all`) vs 0.677 for ML (`clf.ml_macro_f1_all`).
  - ML − rules = −0.126 (`clf.uplift_vs_rules_all`), 95% paired-bootstrap CI −0.173 to −0.050 (`clf.uplift_ci_all`).
  - On plain accuracy the two are not significantly different: McNemar p = 0.243 (`clf.mcnemar_p_all`).
- **Decision (user, 2026-11-16):** the keyword rules are the production classifier (`clf.production_method`); ML is kept as a comparison only.
  - No rule match → UNCLASSIFIED, never forced into OTHER.
  - Precision on accepted predictions is 0.895 (`clf.prod_precision_accepted_all`). Corpus coverage is 0.893 (`clf.corpus_coverage`), so 0.107 of events are Unclassified (`clf.corpus_unclassified_share`).
  - Error analysis: `reports/error_analysis.md`.

## 3. Pareto
- **Views:** counts by product type for the full period and the trailing 60 months, plus severity-weighted (Class I=3, II=2, III=1) and Class-I-only views.
- **Unclassified handling:** a visible last bar, kept inside the denominator.
- **Vital few (to 80%):**
  - Drugs: 8 categories (`pareto.drugs.vital_few_k`) = 0.825 of events (`pareto.drugs.vital_few_share`).
  - Food: 6 categories (`pareto.food.vital_few_k`) = 0.825 (`pareto.food.vital_few_share`).
- **Unclassified share:** 0.035 for drugs (`pareto.drugs.unclassified_share`) and 0.15 for food (`pareto.food.unclassified_share`).
- **Ranking robustness:** rankings are not robust to the weighting. The lowest Kendall tau across views is −0.031 (`pareto.min_kendall_tau`): drugs, count vs Class-I-only, trailing 60 months.

## 4. SPC and trend tests
- **Design** (details in `docs/methodology/time-series.md`):
  - c-chart on monthly counts and p-chart on monthly category share.
  - Laney σ_z widening, applied only when σ_z > 1. It was needed on 0.469 of monitored charts (`spc.laney_share`).
  - Phase I baseline 2015-01..2019-12 (`spc.baseline_window`), with iterative removal of out-of-limit points.
  - Rules: R1 (beyond 3σ) and R2 (8-point run).
- **Coverage:** 16 product-type × category series are monitored (`spc.n_categories`).
- **Signals:** after the baseline, 91 signalled category-months on p-charts (`spc.n_signals`), in 13 of the 16 series (`spc.n_categories_with_signal`).
- **Baseline sensitivity:** signal counts depend strongly on the baseline window (39 to 192 across 4 windows; `reports/tables/spc_window_sensitivity.csv`).
- **False-alarm simulation:** 1,000 stable Poisson series, n = 60.
  - At a mean of 1 event per month, the R1 per-point false-alarm rate is 0.0081 (`spc.sim_lambda1.r1_per_point`), about 3× the 0.0027 normal-theory value.
  - At a mean of 30 it is 0.0018 (`spc.sim_lambda30.r1_per_point`).
  - At a mean of 1, 0.454 of stable 60-month series raise at least one alarm (`spc.sim_lambda1.any_signal_series`).
- **Trend tests:** Poisson GLM, switching to negative binomial when dispersion > 1.5; trailing 60 months; Benjamini-Hochberg correction.
  - 19 series tested (`trend.n_tested`); 0 significant at q < 0.05 (`trend.n_significant_q05`).

## 5. Risk score and backtest
- **Score** (`docs/methodology/risk-score.md`): rank percentiles within product type, weighted momentum 0.35, severity 0.25, SPC signal 0.20, breadth 0.10, volume 0.10.
  - Flag = top quartile AND rising AND ≥ 10 events in 12 months.
  - The definition and success criteria were pre-registered. The document's hash (`risk.preregistration_sha256`) matched at backtest time (`backtest.preregistration_hash_match`).
  - A leakage check on real data passed (`backtest.leakage_check_passed`).
- **Backtest:** 10 yearly origins (`backtest.n_origins`), 17 origin × product-type cells (`backtest.n_cells`).
  - The score's top-3 hit rate (precision@3) was 0.235 (`backtest.p_at_3`).
  - The best baseline was random selection, at 0.382 (`backtest.best_baseline_p_at_3`).
  - Permutation p = 0.999 (`backtest.score_perm_p`).
  - Spearman ρ between score and next-year change = −0.308 (`backtest.spearman_rho`), CI −0.446 to −0.184 (`backtest.spearman_rho_ci`).
  - Momentum alone had ρ = −0.37 (`backtest.momentum_rho`): strong regression to the mean.
  - **Target missed** (`backtest.target_met` = False). The weights were not re-tuned.
- **Sensitivity at 2026-10:**
  - 7 units flagged (`risk.latest_n_flagged`).
  - Median Kendall tau under 1,000 Dirichlet weight draws = 0.735 (`sens.median_tau_weights`).
  - Under 10.5% uniform label noise: 0.606 (`sens.median_tau_label_noise`).
  - With a 6-month window: 0.516 (`sens.tau_window_6m`); with a 24-month window: 0.328 (`sens.tau_window_24m`).
  - Fragile flags: `sens.fragile_flags`.

## 6. Targets: met and missed
| Target (charter / validation plan) | Result | Status |
|---|---|---|
| Classifier macro-F1 ≥ 0.80 (ML candidate) | ML 0.677 | **Missed** |
| ML uplift ≥ +0.10 over rules, CI excluding 0 | −0.126, CI −0.173 to −0.050 | **Missed** (rules better) |
| Precision ≥ 0.90 on accepted predictions | 0.895 (rules) | **Narrowly missed** |
| Label kappa ≥ 0.75 | 0.981 (LLM vs LLM) | Met, but upper bound (L3) |
| Risk-score precision@3 ≥ best baseline + 0.15, and ρ CI > 0 | 0.235 vs 0.382; ρ CI −0.446 to −0.184 | **Missed** |
| Weight-sensitivity median tau ≥ 0.70 | 0.735 | Met |
| Dashboard reconciliation (≥ 5 checks, zero difference) | pending, T6.1.x | Pending |
| Usability ≥ 4/5 tasks per reviewer | pending, T6.1.6 | Pending |

## 7. Limitations (each with its effect on interpretation)
1. **No denominator.** Counts are recall events, not rates; production volume and number of firms are unknown. *Effect:* a rising count may reflect more products or firms, not worse quality. Never read a count as a failure rate.
2. **Selection and enforcement bias.** Data covers only recalls FDA recorded and classified, and FDA priorities, inspection focus and reporting cadence change over time. *Effect:* signals and trends may reflect enforcement, not industry failures. One firm's multi-product sweep can drive a whole month.
3. **LLM-produced labels.** The gold set and the independent check were both LLM annotators. The second annotator saw guide edge cases written by the first, and the same author wrote the keyword rules. *Effect:* kappa 0.981 and rules precision 0.895 are probably optimistic. A human spot check of about 30 events is recommended before publication.
4. **Classifier error and Unclassified share.** About 10% of accepted predictions are wrong, and 15% of food events are Unclassified. *Effect:* category shares carry error. The food Pareto understates categories with vocabulary gaps (e.g., plastic or larvae). Error correlates with category, so it is not just noise.
5. **Stated reason ≠ root cause.** Categories describe FDA's free-text reason, not a verified investigation. *Effect:* "root cause" here means "stated failure mode". It cannot support causal claims.
6. **Small-n backtest.** Only 10 yearly origins and 17 cells. *Effect:* wide intervals. The negative result is consistent across checks, but magnitude estimates are imprecise.
7. **SPC assumptions.** Monthly counts are low and overdispersed, and the baseline window is a choice. *Effect:* textbook false-alarm rates do not hold (see simulation), and signal counts swing 5× with the baseline. Treat signals as prompts to look, not proof.
8. **Reporting lag and date choice.** Report month differs from initiation month (P90 lag 160 days). *Effect:* recent months under-count by initiation date. The primary series uses report date, which shifts timing by months.
9. **Scope exclusions.** No USDA-FSIS (meat, poultry, egg products), devices, cosmetics or biologics review; data starts 2012-06. *Effect:* the analysis is not "all US food recalls". Absence of a category does not mean absence of risk.
10. **Arbitrary severity weights.** Class I/II/III = 3/2/1 is ordinal. *Effect:* severity-weighted rankings depend on the weights. The Class-I-only view changes drug rankings substantially.
11. **Risk-score windows.** The ranking is unstable when the trailing window changes from 12 months to 6 or 24. *Effect:* flags are tied to the 12-month definition; fragile flags are named on the dashboard.
12. **openFDA status field.** Status is recorded at classification time and is not updated. *Effect:* "Ongoing" does not mean currently ongoing; status is not used in any analysis.

## 8. Trace table
| Claim | metrics.json key |
|---|---|
| 47,708 product rows | data.n_product_rows |
| 12,687 events | data.n_events |
| Report dates 2012-06-20..2026-11-04 | data.report_date_min, data.report_date_max |
| Lag P90 160 days | data.lag_p90_days |
| 172 months, 2012-07..2026-10, 12,609 events | series.n_months, series.month_start, series.month_end, series.n_events_in_window |
| Truncation 6 months | series.initiation_truncation_months |
| Gold n = 300; kappa 0.981 | labels.n_gold, labels.kappa_llm_a_vs_b |
| Rules macro-F1 0.802; ML 0.677 | clf.rules_macro_f1_all, clf.ml_macro_f1_all |
| Difference −0.126, CI −0.173..−0.050; McNemar 0.243 | clf.uplift_vs_rules_all, clf.uplift_ci_all, clf.mcnemar_p_all |
| Precision on accepted 0.895; coverage 0.893; Unclassified 0.107 | clf.prod_precision_accepted_all, clf.corpus_coverage, clf.corpus_unclassified_share |
| Vital few 8 / 6, each 0.825 | pareto.drugs.vital_few_k, pareto.food.vital_few_k, pareto.*.vital_few_share |
| Unclassified 0.035 / 0.15 | pareto.drugs.unclassified_share, pareto.food.unclassified_share |
| Min Pareto tau −0.031 | pareto.min_kendall_tau |
| 16 monitored series; 91 signals in 13 | spc.n_categories, spc.n_signals, spc.n_categories_with_signal |
| Laney share 0.469; baseline 2015-01..2019-12 | spc.laney_share, spc.baseline_window |
| False alarm 0.0081 / 0.0018; 0.454 of series | spc.sim_lambda1.r1_per_point, spc.sim_lambda30.r1_per_point, spc.sim_lambda1.any_signal_series |
| 19 trend tests, 0 significant | trend.n_tested, trend.n_significant_q05 |
| Pre-registration hash match; leakage check passed | risk.preregistration_sha256, backtest.preregistration_hash_match, backtest.leakage_check_passed |
| 10 origins, 17 cells | backtest.n_origins, backtest.n_cells |
| precision@3 0.235 vs 0.382; perm p 0.999 | backtest.p_at_3, backtest.best_baseline_p_at_3, backtest.score_perm_p |
| ρ −0.308 (CI −0.446..−0.184); momentum ρ −0.37 | backtest.spearman_rho, backtest.spearman_rho_ci, backtest.momentum_rho |
| Target missed | backtest.target_met |
| 7 flags at 2026-10 | risk.latest_n_flagged |
| Tau 0.735 / 0.606 / 0.516 / 0.328 | sens.median_tau_weights, sens.median_tau_label_noise, sens.tau_window_6m, sens.tau_window_24m |
| Signal range 39–192 across 4 baselines | spc.window_signal_range |
| Weights 3/2/1, 0.35/0.25/0.20/0.10/0.10, 14 categories | definitions (not results): `docs/methodology/risk-score.md`, `data/reference/taxonomy.yaml` |
