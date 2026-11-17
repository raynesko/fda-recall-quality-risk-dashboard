# 1. Project Charter - FDA Recall & Quality Risk Dashboard

**Owner:** solo builder (ISE grad student) | **Duration:** 7-8 weeks at 8-10 h/week (~67.5 h core) | **Tools:** Python (open source), Power BI Desktop (free) or Tableau Public

## Problem statement and business context
Quality and regulatory teams in food and pharma learn from the industry's failures, but public recall records are free-text and scattered. A QA analyst asking "which failure modes are growing, and are they signal or noise?" has no ready answer. openFDA publishes drug and food enforcement (recall) reports with a free-text `reason_for_recall`, FDA classification (Class I/II/III) and dates. This project turns that into a quality-risk intelligence view: classify root causes, find the vital few (Pareto), test whether shifts are special-cause (SPC), score and flag rising failure modes, and recommend DMAIC-framed QA actions.

## Objectives
1. Classify recall reason text into a defined root-cause taxonomy with measured accuracy against a LLM-annotated gold set.
2. Quantify the vital few root causes (Pareto) for drug and food, by count and severity-weighted count.
3. Apply control charts and trend tests to monthly recall activity by category, with validated implementation.
4. Build a transparent risk score and backtest whether it beats naive baselines at flagging rising categories.
5. Deliver a dashboard a non-technical QA reviewer understands in 5 minutes, framed in DMAIC with recommended QA actions.

## Scope (in)
openFDA **drug/enforcement** and **food/enforcement** data; recall-event and product-level modeling; taxonomy + gold set (300 events); keyword baseline vs TF-IDF/logistic-regression classifier; Pareto; c/p control charts with run rules; Poisson-GLM trend tests; risk score + rolling-origin backtest + sensitivity analysis; 4-page dashboard; QA action library; README, methodology, portfolio assets.

## Explicit non-goals
- Not a predictor of individual recalls or of any named firm's quality; no firm-level scoring or accusations.
- No device, biologics-specific, USDA-FSIS (meat/poultry/egg) or international recalls.
- No claim that recall counts are failure *rates* (no production-volume denominator exists).
- No deep-learning/LLM classifier in the core scope (embedding comparison is a P2 stretch).
- Adverse-event (FAERS/CAERS) linkage is stretch context only; no causal inference.
- Not for clinical or regulatory decision use.

## Success metrics (all are **targets**, with justification; actual values will be recorded in `results/metrics.json`)
| # | Metric | Target | Why this target |
|---|---|---|---|
| M1 | Cohen's kappa between two independent LLM annotators on 60 events | >= 0.75 | "Substantial" agreement band (Landis & Koch, 0.61-0.80); a gold set below this is too noisy to evaluate against |
| M2 | Classifier out-of-fold macro-F1 (grouped by firm) | >= 0.80 | Recall text is short and formulaic, especially for drugs; 0.80 is ambitious but plausible for ~14 classes |
| M3 | Uplift over keyword baseline (macro-F1, paired bootstrap CI) | >= +0.10, CI excludes 0 | A smaller gain would not justify ML over Excel-style rules |
| M4 | Precision on accepted predictions at chosen confidence threshold | >= 0.90 | QA users tolerate "Unclassified" better than wrong labels |
| M5 | Control-chart implementation vs hand-calculated values | match within 1e-9; simulated false-alarm rate reported | Proves the SPC code is correct before interpreting signals |
| M6 | Backtest: precision@3 of risk flags vs best naive baseline | >= +0.15 and Spearman CI excludes 0 | Smallest lift a QA lead would find useful; **may be missed** - small n, and a negative result is still reported |
| M7 | Rank stability under random weights (median Kendall tau) | >= 0.70 | Flags should not hinge on arbitrary weights |
| M8 | Usability: tasks completed unaided by non-technical reviewers | >= 4 of 5 each | Dashboard must stand on its own |
| M9 | Reproducibility: clean-environment run + tests | 100% pass | Credibility |

## Assumptions
- openFDA enforcement endpoints and fields remain as documented; verified in T2.1.1 (record counts and date coverage are **not assumed** here).
- `report_date` is an acceptable "month" definition for monitoring; sensitivity uses `recall_initiation_date`.
- An LLM annotator following a written guide can produce a usable gold set if a blind second annotation is measured and the LLM provenance is disclosed.
- ~14 categories suffice; taxonomy may change once after EDA (T3.1.1) and is then frozen.
- Power BI Desktop is available on the builder's Windows machine (decided in T6.1.1).

## Key risks and mitigations
| Risk | L | I | Mitigation |
|---|---|---|---|
| Recall counts misread as quality "rates" | H | H | Metric dictionary, dashboard limitation panel, README limitations; use p-charts on category share |
| Reporting/classification lag distorts recent months | M | M | Default `report_date`; sensitivity with truncation by lag P90 |
| Labeling noise or small gold set | M | H | Labeling guide, relabel + kappa, bootstrap CIs, label-noise sensitivity |
| Backtest has small n -> inconclusive | H | M | Pre-registered plan, report CIs and permutation tests, honest negative result framing |
| One firm dominates a category (artifact) | M | M | Breadth component and min-volume guard in score |
| Scope creep (FAERS, embeddings, more tools) | H | M | P2 tickets never auto-selected; cut order documented |
| openFDA rate limits / API changes | L | M | Prefer bulk download; manifest with hashes; mocked tests |
| Power BI access/sharing problem | M | M | T6.1.1 spike early (week 3); Tableau Public / Plotly fallback; PDF export always |
| Time overrun | M | M | Cut line in milestone plan; weekly demo checkpoints |

## Data sources (to be verified in T2.1.1)
openFDA Drug Enforcement and Food Enforcement endpoints (open.fda.gov/apis) and the bulk downloads page (open.fda.gov/data/downloads). Regulatory references: FDA recall pages, 21 CFR Part 7 Subpart C, 21 CFR 210/211, 21 CFR 117 (all cited from primary sources in T1.1.1; unverified items flagged).
