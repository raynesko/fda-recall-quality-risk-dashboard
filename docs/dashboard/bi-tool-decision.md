# BI Tool Decision (T6.1.1)

Status: research done 2026-11-16; **load test pending (builder must open Power BI Desktop - GUI step).**

## Install
Power BI Desktop installed via `winget install Microsoft.PowerBI` on 2026-11-16 -> `C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe` (verified to exist).

## Data to load
`data/processed/star/*.csv` (UTF-8 with BOM, Excel/Power BI friendly) or `*.parquet` (Power BI supports Parquet via Get Data -> Parquet). Relationships:
- `fact_recall_event[report_date_key]` -> `dim_date[date_key]` (many-to-one)
- `fact_recall_event[firm_key]` -> `dim_firm[firm_key]`
- `fact_recall_event[category_id]` -> `dim_category[category_id]` (after T3.2.4)
- `fact_recall_product[event_id]` -> `fact_recall_event[event_id]` (drill-through)

### Load test the builder runs (criterion 1, ~10 min)
1. Open Power BI Desktop -> Get Data -> Text/CSV -> load the 4 star CSVs (or Parquet).
2. Model view: create the relationships above.
3. Report view: add a line chart, X = `dim_date[month_start]`, Y = Count of `fact_recall_event[event_id]`, legend = `product_type`.
4. Check: total events card = **12,687** (metrics.json `data.n_events`). Save as `dashboard/fda_recall_dashboard.pbix`.

## Sharing options for a reviewer without Power BI (sources checked 2026-11-16)
| Option | Works for this project? | Notes / source |
|---|---|---|
| Power BI "Publish to web" | Probably not | Needs Power BI Pro/PPU for workspaces and an admin-enabled tenant setting; community answers say sign-up needs a work/school account. https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web (community items UNVERIFIED) |
| PDF export from Desktop | Yes (always) | File -> Export -> PDF; static but faithful. |
| Screenshots + 3-min walkthrough video | Yes | Planned in T6.1.6 / T7.2.2. |
| .pbix in the GitHub repo | Yes, for reviewers with Power BI | Data is public, so committing the .pbix is acceptable (check file size). |
| Tableau Public (Desktop Public Edition) | Yes - fallback with a live public link | Free; everything published is public (fine: openFDA data is public); no live connections, extract required; published data may be used for AI training. https://help.tableau.com/current/pro/desktop/en-us/desktop_comparison.htm, https://public.tableau.com/app/data-policy |
| Static Plotly HTML | Yes - last resort | Fully free, hostable on GitHub Pages. |

## Decision (provisional)
**Power BI Desktop** for building (matches job postings in NJ pharma/food QA), shared via **PDF + screenshots + video + .pbix in repo**. If a public interactive link turns out to matter (e.g., for a portfolio site), rebuild the 4 pages in Tableau Public in week 8 only if time allows. Finalize after the builder's load test.
