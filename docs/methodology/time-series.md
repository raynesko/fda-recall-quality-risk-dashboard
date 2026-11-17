# Time-Series and Control-Chart Methodology (T4.2.1, T4.2.2)

All counts are **recall events per month** (event grain, `event_id`), not rates: there is no production-volume denominator. Window values below are recorded in `results/metrics.json` (keys in backticks).

## Month definition (T4.2.1)
- **Primary:** `month` = month of `report_date`, the date FDA posted the recall in the Enforcement Report. It is complete for every event and reflects when the information became available to a monitoring function.
- **Window:** `series.month_start` .. `series.month_end`. Two months are excluded as incomplete:
  - the first month of the data (2012-06), because openFDA enforcement data starts on 2012-06-20;
  - the latest month, because it is still being reported.
  The window holds `series.n_events_in_window` events. The test asserts that this equals the classified events inside the window.
- **Sensitivity series:** month of `recall_initiation_date` (closer to when the failure surfaced).
  - Recently initiated recalls are not yet reported. The P90 of report lag is `data.lag_p90_days` = 160 days, so the last **N = ceil(160 / 30.44) = 6 months** are truncated (`series.initiation_truncation_months`).
  - The series starts in the same month as the primary series. Events initiated before that month are excluded, which removes older recalls reported after 2012-06.
- **Grid:** every month × product_type × category, including UNCLASSIFIED, with zeros filled.
  - Columns: `n_events`, `n_class1`, `month_total` (all categories of that product type), `share` = `n_events / month_total`.
  - Files: `data/processed/series_monthly.parquet` (primary) and `series_monthly_initiation.parquet` (sensitivity).

## Control charts (T4.2.2)
**What the limits mean:** the limits describe the *stability of FDA-recorded recall activity* for a category. They say nothing about any firm's quality, and a signal is not a failure rate. A signal means "this month's recall activity is unusual relative to the baseline period". It can reflect industry failures, FDA enforcement focus (for example, a sweep of one firm's many products) or reporting cadence.

- **c-chart** on monthly event counts. CL = mean count c̄ in Phase I; limits c̄ ± 3·√c̄.
- **p-chart** on category share of that month's events (adjusts for overall volume swings). p̄ = Σx / Σn over Phase I; σᵢ = √(p̄(1−p̄)/nᵢ); limits vary with nᵢ.
- **Laney adjustment** (both charts). Compute zᵢ = (valueᵢ − CL)/σᵢ on Phase I and σ_z = mean moving range of z / 1.128.
  - If σ_z > 1 (overdispersion), the limits are widened to CL ± 3·σᵢ·σ_z.
  - If σ_z ≤ 1, the textbook limits are kept (the limits are never narrowed).
- **LCL floored at 0.**
- **Phase I baseline:** default 2015-01..2019-12 (configurable).
  - Points beyond the limits are removed iteratively and the limits recomputed, up to 10 passes.
  - Every removed month is logged in `reports/tables/spc_phase1_removed.csv`.
  - Only rule-1 points are removed; run-rule points are not removed.
- **Phase II:** all months after the baseline. The rules are also evaluated on baseline months, for display.
- **Rules:**
  - **R1:** a point beyond a control limit.
  - **R2:** 8 consecutive points on the same side of the CL. The 8th point and every later point in the run are flagged.
- **Monitored series:** product_type × category with a Phase I mean ≥ 1 event per month. UNCLASSIFIED is charted as a data-quality series but excluded from the signal counts.
- **False-alarm calibration:** textbook 3-sigma limits assume normality. For Poisson counts with small means, the real false-alarm rate differs. It is measured by simulation (1,000 stable Poisson series, n = 60, several means) using the exact same chart code, including Laney. Results are recorded as `spc.sim_*`.
- **Sensitivity:** signal counts under 3 alternative baseline windows are reported side by side in `reports/tables/spc_window_sensitivity.csv`.
