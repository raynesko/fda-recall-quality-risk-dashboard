# 8. Portfolio Packaging (planning draft - FINAL versions live in docs/portfolio/ as of 2026-11-17)

## Resume bullets (Action + method + quantified result)
Status 2026-11-16: classifier and backtest results are in. Both ML/predictive targets were **missed**, so the bullets below are worded around what was evaluated. Every number traces to `results/metrics.json`; the key is in brackets and is deleted before use.

1. **Classified 12,687 FDA drug and food recall events into 14 root-cause categories** with a keyword-rule classifier that outperformed a TF-IDF + logistic-regression model on a 300-event LLM-annotated gold set (macro-F1 0.80 vs 0.68, paired-bootstrap 95% CI of difference −0.17 to −0.05; firm-grouped CV) and covers 89% of events at 0.90 precision on accepted predictions. [clf.corpus_n_events, clf.rules_macro_f1_all, clf.ml_macro_f1_all, clf.uplift_ci_all, clf.corpus_coverage, clf.prod_precision_accepted_all (0.895 rounds to 0.90; say "~0.90")]
2. **Applied Pareto analysis and Laney-adjusted p/c control charts** to 172 months of recall data. 8 of 13 drug categories and 6 of 13 food categories account for 82% of events. SPC simulation showed textbook 3-sigma limits raise ~3× more false alarms on low-count series. [pareto.drugs.vital_few_k, pareto.food.vital_few_k, pareto.*.vital_few_share, series.n_months, spc.sim_lambda1.r1_per_point vs 0.0027]
3. **Pre-registered and backtested a transparent quality-risk score** against 3 naive baselines over 10 yearly origins. It did not beat them: regression to the mean made recent momentum anti-predictive (ρ = −0.37). I reported the miss rather than re-tuning, and delivered it as a triage view in a 4-page Power BI dashboard with DMAIC-framed QA actions. [backtest.n_origins, backtest.target_met, backtest.momentum_rho; dashboard pages once T6.1.x done]

Do not write: "predicts recalls", "reduced", "saved", or anything implying intervention.

## 60-second interview pitch (fill in numbers)
"I'm an industrial and systems engineering grad student with a software background, and I wanted a project in the language of quality. FDA publishes every drug and food recall with a free-text reason, but nobody can see at a glance which failure modes are growing. I classified [N] recall reasons into [14] root-cause categories - validating against a 300-event gold set labeled by an LLM annotator and cross-checked by a second, independent annotator - then used a Pareto to find the vital few, and control charts to separate genuine shifts from normal month-to-month noise. I tested an ML classifier against a keyword baseline, and the baseline won, so that's what runs in production. I also built a risk score, pre-registered its success criteria, and backtested it against simple baselines. It didn't beat them, because categories that just spiked tend to fall back (regression to the mean). So I present it as a triage view, not a forecast. Everything is in a Power BI dashboard framed in DMAIC with recommended QA actions like supplier verification or environmental-monitoring review. Counts are recall events, not failure rates, and I'm upfront about that limitation."

## 5-slide summary outline
1. **Problem & question** - why recall root causes matter to QA; the data (openFDA drug + food enforcement); scope and non-goals.
2. **Method** - pipeline diagram; taxonomy; DMAIC mapping.
3. **Classification results** - baseline vs ML table, kappa, confusion highlights, confidence/Unclassified policy.
4. **Pareto + SPC findings** - vital few chart; one control chart with a special-cause signal and plain-language interpretation.
5. **Risk score, backtest & recommendations** - watchlist, backtest honesty, sensitivity, DMAIC actions, limitations.

## Five likely interview questions with talking points
1. **"Why not just count recalls per month - what's the point of control charts?"** Month-to-month counts fluctuate by chance; a control chart separates common-cause from special-cause variation so you don't chase noise (Deming). I used p-charts on category share because there's no production denominator, and simulated false-alarm rates because small Poisson means distort textbook limits.
2. **"Are these recall *rates*?"** No - events per month with no volume denominator. FDA also classifies and posts on its own cadence, so counts reflect enforcement/reporting as well as industry failures. I reported that limit on the dashboard and README.
3. **"How did you validate the classifier / how do you know labels are right?"** 300-event gold set labeled by an LLM annotator; an independent second annotator relabeled 60 blind (kappa [K]). Both are LLMs, so I treat agreement as an upper bound and recommend a human spot check. Cross-validation grouped by firm to avoid near-duplicate leakage. Baseline written before looking at gold labels. Below-threshold predictions are `Unclassified`, not forced.
4. **"What would a QA manager do with this?"** Walk the watchlist: e.g., a rising undeclared-allergen category -> review label control and changeover cleaning verification; microbial -> environmental monitoring and supplier verification; each action framed Define-Measure-Analyze-Improve-Control with the owner function. Distinguish correction vs corrective action vs CAPA. Actions are hypotheses from category patterns, not findings on any firm.
5. **"Did the risk score work? What would you change?"**
   - No, against its pre-registered target. Precision@3 was 0.24 vs 0.38 for random, over 10 yearly origins and 17 cells, and Spearman ρ was −0.31.
   - Momentum alone had ρ −0.37 with next-year change: a textbook regression-to-the-mean effect.
   - I didn't re-tune weights to pass. Its value is as a transparent triage view (severity, SPC signals, breadth), and the sensitivity analysis shows which flags are fragile.
   - Also ready: "Why did ML lose?" 300 labels over 14 classes is too few for the rare classes (PACKAGING/OTHER F1 0), while recall reasons are formulaic enough for rules. Caveat: the same annotator wrote the rules and the labels. Regression to the mean makes naive momentum a strong baseline, which is why I included it. Next steps: add a volume denominator (e.g., establishment counts) if a defensible public source exists, and expand labels with a second annotator.

Also be ready for: Class I vs II vs III definitions; difference between voluntary recall and FDA-requested/mandatory; cGMP vs HACCP/HARPC; why logistic regression over a transformer (small labeled set, interpretability, auditability in a regulated setting).
