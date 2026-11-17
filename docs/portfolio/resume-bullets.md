# Resume Bullets (T7.2.1)

Every number is printed by `python scripts/resume_numbers.py` with its `results/metrics.json` key. All are *achieved* values. Each bullet fits within 2 lines at standard resume width (11 pt, 0.75" margins); check this in your template.

**FDA Recall & Quality Risk Dashboard** | Python, scikit-learn, statsmodels, Power BI | github.com/<you>/fda-recall-quality-risk-dashboard

- Classified **12,687** FDA drug/food recall events into 14 root-cause categories. A keyword-rule model beat TF-IDF + logistic regression (macro-F1 **0.80 vs 0.68**) on a 300-event gold set.
- Applied Pareto and Laney-adjusted p/c control charts to **172 months** of recall data: **8 of 13** drug and **6 of 13** food categories account for **82%** of events.
- Pre-registered and backtested a quality-risk score against 3 baselines over **10 yearly origins**. Reported that it missed its target (regression to the mean), and shipped it as a DMAIC triage view in a 4-page Power BI dashboard.

Trace: bullet 1 → `clf.corpus_n_events`, `clf.rules_macro_f1_all`, `clf.ml_macro_f1_all`, `labels.n_gold`. Bullet 2 → `series.n_months`, `pareto.drugs.vital_few_k`, `pareto.food.vital_few_k`, `pareto.*.vital_few_share`. Bullet 3 → `backtest.n_origins`, `backtest.target_met`.

**Alternate wording if space allows:**
- Validated classifier labels with a second independent annotator (kappa 0.98) → `labels.kappa_llm_a_vs_b`. **Say "LLM-annotated" if asked.** Never write "hand-labeled".
- Showed by simulation that textbook 3-sigma limits raise 3× the expected false alarms on low-count series → `spc.sim_lambda1.r1_per_point` = 0.0081 vs 0.0027.

**Do not write:** "predicts recalls", "reduced recalls", "saved", or "ML classifier achieved…" (the rules won).
