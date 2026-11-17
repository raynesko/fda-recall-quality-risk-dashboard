# 5-Slide Summary (T7.2.1)

1. **Problem and data.**
   - Why recall root causes matter to QA.
   - Data: openFDA drug + food enforcement, 12,687 events, 2012-06 to 2026-11.
   - Unit = recall event; counts, not rates.
   - Out of scope: USDA-FSIS, devices, firm-level judgments.
   - *Visual:* pipeline diagram (README §2).
2. **Measure: can we classify reliably?**
   - 14-category taxonomy; 300-event LLM-annotated gold set, two-annotator kappa 0.98 (upper bound).
   - Keyword rules 0.80 vs ML 0.68 macro-F1. The rules won and are in production; Unclassified is shown, never forced.
   - *Visual:* classifier table + confusion highlights (`reports/classifier_eval.md`, `reports/error_analysis.md`).
3. **Analyze: Pareto and control charts.**
   - 8 drug / 6 food categories = 82% of events.
   - p-chart example (Drugs IMPURITY, 2018-2021 signals).
   - False-alarm simulation: 3× the textbook rate at low counts.
   - No significant 5-year trends after FDR correction.
   - *Visuals:* `pareto_food_full.png`, `spc_drugs_impurity.png`.
4. **Improve: risk score and honest backtest.**
   - Pre-registered score (5 components).
   - Backtest: precision@3 0.235 vs 0.382 random; momentum ρ −0.37 → regression to the mean. Target missed; not re-tuned.
   - Weight sensitivity tau 0.74; 7 current flags, 5 of them fragile.
   - *Visual:* `risk_rank_stability.png`.
5. **Control: dashboard, actions and limitations.**
   - 4-page Power BI dashboard (executive, Pareto, control charts, watchlist) with reconciliation.
   - DMAIC QA action library: 60 actions, 56 citations verified to the 21 CFR section.
   - Top limitations: no denominator, enforcement bias, LLM labels.
   - Next steps: human label check, denominator source, rule v2 on a fresh holdout.
