# 4. Milestone Plan

Capacity assumption: 8-10 h/week. Core backlog = 67.5 h -> **7 weeks at ~9.5 h or 8 weeks at ~8.5 h**. The 8-week plan below leaves slack in weeks 1, 4, 7, 8. A genuine 6-week finish is not realistic without cutting P1 work (see cut line).

| Wk | Tickets (hours) | Load | Demo-able checkpoint (end of week) |
|---|---|---|---|
| 1 | T1.1.1 (2.5), T1.1.2 (2), T1.1.3 (1.5), T2.1.1 (1.5) | 7.5 | Recall primer + taxonomy v1 + DMAIC/metric dictionary + verified openFDA source notes |
| 2 | T2.1.2 (3.5), T2.1.3 (4), T2.2.1 (2.5) | 10 | `python -m fda_recall.ingest` rebuilds raw->clean->star; data-quality report with counts and lag |
| 3 | T3.1.1 (1.5), T3.1.2 (4), T3.2.1 (2), T6.1.1 (1) | 8.5 | 300-event gold set labeled; keyword baseline macro-F1 table; BI tool decided and first visual rendered |
| 4 | T3.1.3 (1), T3.2.2 (3), T3.2.4 (2.5), T4.1.1 (1.5) | 8 | Kappa + ML vs baseline with CIs; full corpus classified; first Pareto chart |
| 5 | T4.2.1 (1.5), T4.2.2 (3.5), T4.2.3 (1.5), T5.1.1 (3) | 9.5 | Validated control charts with signals; trend table; **pre-registered** risk-score doc |
| 6 | T5.1.2 (3.5), T5.1.3 (2), T6.1.2 (2), T6.1.3 (1.5) | 9 | Backtest report (honest result) + sensitivity; dashboard pages 1-2 |
| 7 | T6.1.4 (2), T6.1.5 (2), T6.2.1 (2), T6.1.6 (1), T7.1.2 (1.5) | 8.5 | Full 4-page dashboard + DMAIC action library + usability log + methodology doc |
| 8 | T7.1.1 (2), T7.1.3 (2), T7.2.1 (2.5) (+~3 h buffer) | 6.5 | README, clean-environment run, resume assets from verified numbers |

Stretch (only if ahead, in this order): T7.2.2 video (1) -> T3.2.3 embeddings (2) -> T2.3.1 AE spike (1.5) -> T2.3.2 AE context (2.5).

## Critical path
T2.1.1 -> T2.1.2 -> T2.1.3 -> T3.1.2 (labeling) -> T3.1.3 -> T3.2.2 -> T3.2.4 -> T4.2.1 -> T4.2.2 -> T5.1.1 -> T5.1.2 -> T5.1.3 -> T6.1.5 -> T7.1.2 -> T7.1.3 -> T7.2.1.
Labeling (T3.1.2, 4 h of manual work) and the 5-day gap before relabeling (T3.1.3) are the least compressible items - **start labeling by the first day of week 3**. The BI spike (T6.1.1) is deliberately early so a tool/sharing problem surfaces in week 3, not week 7.

## If time runs short - cut line (in order)
1. Drop P2 stretch work (already excluded from the 67.5 h).
2. Cut T4.2.3 trend tests (-1.5 h): Pareto + SPC still tell the story.
3. Cut T6.1.6 usability test to one informal reviewer (-0.5 h).
4. Reduce T5.1.3 to the Dirichlet-weights analysis only (-1 h).
5. Reduce T3.1.3 relabel to 30 events (-0.5 h) and caveat it.
6. Merge dashboard pages 2 and 3 into one (-1 h).
Never cut: gold set, baseline comparison, SPC validation tests, pre-registration, backtest (even if the result is negative), limitations text, `record_metric` discipline.

## Weekly ritual (15 min)
Run `python scripts/tickets.py list --week N`, update statuses, note actual hours in each ticket's Agent log, re-plan the next week with actuals. Compare cumulative actual vs planned hours; if more than 15% over after week 3, apply cut line item 2 immediately.
