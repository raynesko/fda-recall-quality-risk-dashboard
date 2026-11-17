# 9. Risks and Open Questions

Nothing here blocks starting. Each has a default assumption; change it by editing this file and telling the agent.

| # | Question | Default assumption (if you don't answer) |
|---|---|---|
| Q1 | Power BI or Tableau Public? Power BI Desktop is free on Windows but sharing usually needs a work/school licence; Tableau Public gives a free public link but all data is public. | **Power BI Desktop** + PDF/screenshots/video for sharing; T6.1.1 re-decides in week 3 based on what actually works for you |
| Q2 | Include devices? | **No** (drug + food only; devices are a non-goal) |
| Q3 | Treat USDA-FSIS meat/poultry recalls? | **Out of scope**, flagged as a limitation; not in openFDA |
| Q4 | Will you have a second person to label ~60 events for true inter-rater agreement? | **No** - LLM-produced labels, inter-annotator (LLM) kappa only, caveated |
| Q5 | Use `report_date` or `recall_initiation_date` as the month? | **report_date** primary, initiation date as sensitivity |
| Q6 | OK to read the backtest as a possible *negative* result and still publish it? | **Yes** - negative result is reported plainly; resume bullet wording changes |
| Q7 | Severity weights (Class I=3, II=2, III=1) acceptable? | Yes, with Class-I-only sensitivity shown |
| Q8 | Is adverse-event (FAERS) context worth the time? | **No** (P2 stretch, only if ahead of schedule) |
| Q9 | Should this repo be public on GitHub? | **Yes**, with no raw data committed and a disclaimer; confirm no employer/school restrictions |
| Q10 | Weekly hours: can you reliably do ~9.5 h? | Plan is 8 weeks at ~8.5 h; compress to 7 only if you hit 9.5 h |

## Residual risks to watch
- **Regulatory terminology errors** - the biggest credibility risk with QA hiring managers. Every citation is verified in T1.1.1/T6.2.1 or marked UNVERIFIED; consider having a QA contact skim the glossary and action library.
- **Facts not yet verified (do not rely on until T2.1.1/T1.1.1 confirm):** exact openFDA field availability, record counts, date coverage, rate limits, bulk download structure, and whether biologics appear. This plan deliberately contains no such numbers.
- **Backtest power** is low (few categories x few non-overlapping origins). The plan reports CIs and permutation tests rather than promising significance.
- **Over-claiming** - avoid "predicts", "reduces", or firm-specific statements anywhere.
