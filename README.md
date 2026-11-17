# FDA Recall & Quality Risk Dashboard

**Which stated failure modes drive FDA drug and food recalls, which are shifting beyond normal variation, and what should a QA function look at?** This repo answers that from public openFDA enforcement data. It classifies recall reasons into root-cause categories, applies Pareto, control charts and trend tests, evaluates a transparent risk score against naive baselines, and frames the result in DMAIC with QA actions. The output is a 4-page Power BI dashboard.

![Food recall Pareto](reports/figures/pareto_food_full.png)

> Dashboard screenshots go in `docs/dashboard/screens/` after the Power BI test (`docs/dashboard/test-checklist.md`).

**Headline results** (all *achieved* values, from `results/metrics.json`):

| | Result | Key |
|---|---|---|
| Recall events analyzed | **12,687** drug + food events (report dates 2012-06-20 to 2026-11-04) | `data.n_events`, `data.report_date_min/max` |
| Vital few | **8 of 13** drug categories and **6 of 13** food categories account for **82.5%** of events | `pareto.*.vital_few_k`, `pareto.*.vital_few_share` |
| Risk score backtest | **Did not beat** naive baselines (precision@3 0.235 vs 0.382 for random), so it is reported as a triage view, not a forecast | `backtest.p_at_3`, `backtest.best_baseline_p_at_3`, `backtest.target_met` |

## 1. Problem
QA and regulatory-intelligence teams in food and pharma want to learn from industry recalls. Each FDA enforcement record holds a free-text `reason_for_recall`, so seeing patterns means reading thousands of records. This project turns those records into a classified, statistically monitored view.

It measures **FDA-recorded recall events**. These are counts, not failure rates, and the project says nothing about any individual firm.

## 2. Method
```
openFDA bulk download -> clean & dedupe to events -> classify reason (keyword rules) -> Pareto
   -> monthly series -> c/p control charts (Laney) + trend tests -> risk score -> backtest + sensitivity
   -> DMAIC QA action library -> dashboard tables -> generated Power BI project (PBIP)
```
- **Data:** openFDA drug and food enforcement endpoints, bulk files. Raw files are immutable, with a SHA-256 manifest. Product rows are deduplicated to the recall-event grain. Details: `docs/data/`.
- **Taxonomy:** 14 categories of stated failure mode with tie-break priority (`data/reference/taxonomy.yaml`, `docs/domain/root-cause-taxonomy.md`).
- **Classification:** a frozen keyword-rule baseline was compared with TF-IDF + logistic regression on a 300-event LLM-annotated gold set (`labels.n_gold`), using cross-validation grouped by firm.
  - **The rules won:** macro-F1 0.802 vs 0.677 (`clf.rules_macro_f1_all`, `clf.ml_macro_f1_all`). They are the production classifier.
  - Events no rule matches are shown as **UNCLASSIFIED**, never forced into a category.
- **Pareto:** count, severity-weighted and Class-I-only views, with ranking robustness measured by Kendall tau.
- **SPC:**
  - c-chart on monthly counts and p-chart on category share, with Laney adjustment for overdispersion. Phase I baseline 2015-01..2019-12; rules R1 (beyond limit) and R2 (8-point run).
  - False-alarm rates were measured by simulation, because textbook 3-sigma rates do not hold for low counts.
- **Trend tests:** Poisson or negative-binomial GLM with Benjamini-Hochberg correction.
- **Risk score:** transparent weighted percentiles of momentum, severity, SPC signal, breadth and volume.
  - **Pre-registered** before any backtest; the document's hash was recorded (`risk.preregistration_sha256`).
  - Backtested over 10 yearly origins against volume, momentum and random baselines.
  - Sensitivity checks: weights, window length and label noise.
- **DMAIC:** 12 categories × 5 phases of QA actions with owner, metric and CFR citation. 56 of 60 citations were verified (`docs/domain/qa-action-library.md`).

Full write-up: `docs/methodology/methodology-and-limitations.md`.

## 3. Results
**Classification.** Values are on the gold set unless noted.

| Model | Macro-F1 | Note |
|---|---|---|
| Keyword rules (production) | 0.802 | precision on accepted predictions 0.895; 0.893 of all events classified (`clf.prod_precision_accepted_all`, `clf.corpus_coverage`) |
| TF-IDF + logistic regression | 0.677 | difference −0.126, 95% CI −0.173 to −0.050 (`clf.uplift_ci_all`) |

Label agreement between two independent LLM annotators: kappa 0.981 on 60 events (`labels.kappa_llm_a_vs_b`). Treat this as an upper bound; see limitation 3.

**Pareto.**
- Drugs: impurity, specification failure, sterility, potency, foreign material, labeling, mix-up and CGMP make up the vital few (`pareto.drugs.vital_few`).
- Food: allergen, microbial, foreign material, labeling, process/sanitation and impurity (`pareto.food.vital_few`).
- Unclassified: 0.15 of food events and 0.035 of drug events (`pareto.*.unclassified_share`).

**Control charts and trends.**
- 16 series are monitored (`spc.n_categories`).
- After the baseline, 91 p-chart signals across 13 series (`spc.n_signals`, `spc.n_categories_with_signal`). This count swings from 39 to 192 depending on the baseline window (`spc.window_signal_range`).
- Simulation: at 1 event per month, rule-1 false alarms run 0.0081 per point, against the textbook 0.0027 (`spc.sim_lambda1.r1_per_point`).
- No category trend is significant after correction (`trend.n_significant_q05` = 0 of 19).

![Control chart example](reports/figures/spc_drugs_impurity.png)

**Risk score (honest negative result).**
- precision@3: 0.235 vs 0.382 for random selection.
- Spearman ρ between score and next-year change: −0.308, 95% CI −0.446 to −0.184 (`backtest.spearman_rho`, `_ci`).
- Momentum alone had ρ −0.37 (`backtest.momentum_rho`): categories that just rose tended to fall back (**regression to the mean**).
- Target **missed** (`backtest.target_met`). The weights were not re-tuned. The score is used to triage attention.
- Weight sensitivity: median tau 0.735 (`sens.median_tau_weights`). 7 categories are currently flagged (`risk.latest_n_flagged`), and fragile flags are named on the dashboard.

**Targets** (from `docs/01-project-charter.md`; *target* ≠ *achieved*):
- Missed: ML macro-F1 ≥ 0.80, ML uplift ≥ +0.10, precision on accepted predictions ≥ 0.90 (narrowly), and risk-score lift ≥ +0.15.
- Met: kappa ≥ 0.75 (upper bound) and weight-sensitivity tau ≥ 0.70.
- Pending: dashboard reconciliation and usability.

## 4. How to run
Requires Windows, macOS or Linux with Python 3.12. Power BI Desktop is needed only for the dashboard.
```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt     # pinned; full lock in requirements-lock.txt
python scripts/run_pipeline.py --download   # fetch openFDA bulk files, then run all 17 steps (~4 min after download)
pytest -q                           # 71 tests
python scripts/resume_numbers.py    # every published number with its metrics key
```
- **Dashboard:** open `dashboard/FDA_Recall_Dashboard.pbip` in Power BI Desktop, then click **Refresh**.
  - The project is generated by `python -m fda_recall.pbip`.
  - Validate it with `python scripts/validate_pbir.py` (JSON schemas) and `powershell -File scripts\validate_tmdl.ps1` (TMDL).
- **Optional API key:** set the environment variable `OPENFDA_API_KEY`. Never commit it.
- **Backlog for agents:** `python scripts/tickets.py next` (see `CLAUDE.md`).

## 5. Assumptions
- **Unit:** the recall event (`event_id`); one event can cover many products.
- **Month:** `report_date` month (when FDA posted the recall). Initiation-date month is a sensitivity series with a 6-month truncation from the 160-day P90 reporting lag (`data.lag_p90_days`).
- **Severity weights:** Class I/II/III = 3/2/1 (ordinal, arbitrary), always shown alongside a Class-I-only view.
- **Categories:** describe FDA's *stated* reason, not a verified root cause.
- **Risk-score weights:** 0.35/0.25/0.20/0.10/0.10, chosen a priori and not tuned.

## 6. Limitations
1. **No denominator:** counts are not failure rates.
2. **Selection and enforcement bias:** FDA priorities and reporting cadence shape the data.
3. **LLM-produced labels:** both annotators were LLMs, and the same author wrote the rules, so accuracy and kappa are likely optimistic. A human spot check is recommended.
4. **Classifier error:** about 10% of accepted predictions are wrong; 15% of food events are Unclassified.
5. **Stated reason ≠ root cause.**
6. **Small-n backtest:** 10 origins.
7. **SPC is baseline-dependent:** low counts inflate false alarms.
8. **Reporting lag:** see Assumptions.
9. **Scope:** excludes USDA-FSIS meat, poultry and egg products, devices and biologics; data starts 2012-06.
10. **Arbitrary severity weights.**
11. **Window-dependent risk ranking.**
12. **Status field:** recorded at classification time and not updated.

Details and their effect on interpretation: `docs/methodology/methodology-and-limitations.md`.

## Repo map
`src/fda_recall/` pipeline package · `scripts/` pipeline runner, validators, ticket CLI · `tests/` pytest · `data/reference/` taxonomy, keyword rules, QA action library · `data/labels/` gold set · `reports/` generated reports, figures and tables · `results/metrics.json` the single source of every published number · `dashboard/` Power BI project · `docs/` charter, plan, domain, methodology, dashboard · `tickets/` backlog.

## Data sources and citations
- openFDA drug enforcement and food enforcement APIs: https://open.fda.gov/apis/ (public domain; see openFDA terms).
- Regulatory structure: 21 CFR Parts 7, 211 and 117 via the Cornell LII mirror. Section-level verification status is in `docs/domain/fda-recall-primer.md` and `docs/domain/qa-action-library.md`.

## Disclaimer
This is a portfolio project built on public openFDA data and **not for clinical or regulatory decisions**. Patterns describe categories of FDA-recorded recall events, not the quality of any named firm. openFDA data may be incomplete or delayed; FDA does not endorse this work.
