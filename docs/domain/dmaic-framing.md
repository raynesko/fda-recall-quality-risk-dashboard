# Problem Statement and DMAIC Framing (T1.1.3)

## Problem statement
A QA/regulatory-intelligence function in a NJ food or pharma manufacturer wants to learn from industry recalls: which stated failure modes drive FDA recalls, which are growing beyond normal variation, and what preventive QA actions follow. Today that requires reading thousands of free-text enforcement records (12,687 events, 2012-06 to 2026-11, per `results/metrics.json` keys `data.n_events`, `data.report_date_min/max`). The "process" improved here is the **recall root-cause monitoring process** itself: from manual reading to a classified, statistically monitored and backtested view.

Scope boundary: the process monitors FDA-recorded recall **events**; it does not measure any firm's internal quality, and counts are not failure rates (no production denominator).

## DMAIC mapping
| Phase | Question | Project components | Tickets |
|---|---|---|---|
| **Define** | What do QA users need from recall data, and what is in scope? | Charter, CTQ tree, taxonomy, metric dictionary, recall primer | T1.1.1-T1.1.3, charter |
| **Measure** | Can we measure stated root cause reliably and reproducibly? | Ingest + cleaning with data-quality report; gold set + kappa (measurement system analysis for labels); keyword baseline vs classifier accuracy | T2.1.x, T2.2.1, T3.1.x, T3.2.x |
| **Analyze** | Which causes dominate, and which are shifting? | Pareto (vital few), c/p control charts with run rules, trend tests with FDR control | T4.1.1, T4.2.x |
| **Improve** | What should QA do differently? | Risk score + watchlist, backtested against naive baselines; DMAIC QA action library per failure mode | T5.1.x, T6.2.1 |
| **Control** | How is the gain sustained? | Control charts as the ongoing monitor, weekly refresh from openFDA, dashboard with reconciliation, documented reaction plan (signal -> review -> action library) | T4.2.2, T6.1.x, T7.1.3 |

Note on "Improve": this project cannot change recall outcomes. The improvement is to the *monitoring process* (speed, consistency, false-alarm control), and the QA actions are recommendations for a manufacturer's own process.

## CTQ tree
| Customer need | Driver | CTQ (measurable spec) - all **targets** |
|---|---|---|
| Trustworthy categories | Classification accuracy | Macro-F1 >= 0.80 on gold set; precision >= 0.90 on accepted predictions; Unclassified share reported |
| Consistent measurement | Label reliability | Kappa between two independent LLM annotators >= 0.75 (upper bound; human spot check recommended) |
| Timely detection without chasing noise | Signal quality | Control-chart false-alarm rate measured by simulation and reported; data refresh within 1 week of openFDA update |
| Useful prioritization | Risk flag value | Backtest precision@3 >= best naive baseline + 0.15 (may be missed; reported either way) |
| Traceable evidence | Auditability | 100% of published numbers trace to `results/metrics.json`; dashboard reconciles to Python (0 difference on >= 5 checks) |
| Usable by non-technical reviewers | Clarity | >= 4 of 5 usability tasks completed unaided by each of 2 reviewers |

## Month definition
`report_month` = month of **`report_date`** (when FDA posted the recall in the Enforcement Report). Reason: it is complete for every row (0 invalid), it reflects when the information became available to a monitoring function, and it avoids recent-month under-counting caused by reporting lag. Sensitivity alternative: month of `recall_initiation_date` (closer to when the failure surfaced), with the most recent N months truncated, where N comes from the lag P90 (`data.lag_p90_days` = 160 days -> N = 6 months; finalised in T4.2.1). The current partial month is always excluded.
