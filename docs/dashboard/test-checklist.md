# Dashboard Test Checklist (for you, at the end - about 60-90 minutes)

The dashboard is a **generated Power BI project** (`dashboard/FDA_Recall_Dashboard.pbip`), built by `python -m fda_recall.pbip` from the Python outputs.

**Checked before handover:**
- All 45 report JSON files validate against Microsoft's published PBIR schemas (`python scripts/validate_pbir.py`).
- The TMDL model parses with Microsoft's own TMDL deserializer from your Power BI install (`powershell -File scripts\validate_tmdl.ps1`).

**Not yet checked** (this needs you): Power BI actually rendering it, the DAX formulas returning the right values, and the visuals looking right.

## 0. Open (5 min)
1. Double-click `dashboard\FDA_Recall_Dashboard.pbip`. If Power BI warns about an older or newer format, accept.
2. If tables are empty, click **Home > Refresh**. Data loads from `data\processed\` through the `DataFolder` parameter.
   - If you moved the repo, change the folder in **Transform data > Edit parameters**.
3. If anything errors, copy the exact message into `docs/dashboard/test-results.md` and tell the agent. Errors are fixed in the generator, not by hand, so that every fix survives the next regeneration.

## 1. Reconciliation (criterion for T6.1.2-T6.1.5; 15 min)
Fill in the *Dashboard value* and *Pass* columns in `docs/dashboard/reconciliation.md`. Clear all slicers first.

| Page | What to read |
|---|---|
| 1 Executive | the four cards (events last 12 months, change, Class I share, flagged). For Drugs, set the product slicer to Drugs |
| 2 Pareto | hover the first bar of each chart; hover the UNCLASSIFIED bar on the Food chart |
| 3 Control charts | the "Signalled months" card with no series selected, which shows the default series. A table of p-chart signals across all series is on the page |
| 4 Watchlist | the score of each FLAGGED row; count of flagged rows |

The pass rule is an identical value. Rounding differences in display formatting count as a pass only if the underlying value matches (check with the visual's tooltip).

## 2. Page checks (15 min)
- [ ] **P1:** Each slicer (product type, FDA class, report date) changes the cards and the trend line. The "Data as of" footer is visible. The trend line has a legend, so it does not rely on color alone.
- [ ] **P2:** Bars run largest to smallest with **UNCLASSIFIED last**. The cumulative-% line reaches 100%. Switching *Weighting* to `severity` and `class1` reorders the bars. Clicking a bar filters the event table.
- [ ] **P3:**
  - The *Chart type* slicer switches between Count (c) and Share (p).
  - Picking another series updates the chart and the signal card.
  - Signal points are visible (markers). If markers are missing, report it.
  - The explanation box is readable.
  - The 6 small multiples render.
- [ ] **P4:** Rows sort by score. FLAGGED rows show "Why flagged" and "Stability %". Clicking a row filters the QA-actions table. The limitations panel and the disclaimer are visible.

## 3. Usability test (T6.1.6; 2 reviewers × ~10 min)
Give each non-technical reviewer these 5 tasks. Do not help. Record yes/no, time and a quote in `docs/dashboard/usability-log.md`, using initials only.
1. Which root-cause category has the most drug recall events?
2. Roughly what share of food recall events are allergen-related?
3. On the control-chart page, what does a highlighted (signal) point mean?
4. Which categories are currently flagged, and why is one of them flagged?
5. What QA action is suggested for one flagged category?

Target: ≥ 4 of 5 tasks unaided per reviewer. Note the top 3 confusions; the agent will fix them in the generator.

## 4. Export (10 min)
- **File > Export > Export to PDF** → save as `docs/dashboard/dashboard.pdf`.
- Take ≥ 6 screenshots (one per page plus a P3 series switch and a P4 row selection) → `docs/dashboard/screens/`.
- **File > Save.** Power BI may add cache files; `.gitignore` already excludes `.pbi/` and `cache.abf`.
