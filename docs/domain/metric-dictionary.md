# Metric Dictionary (T1.1.3)

Every metric used in code, dashboard or resume is defined here first. "Grain" = level at which it is counted. Source fields refer to `data/processed/recalls_event.parquet` / `recalls_product.parquet` / star schema.

| # | Metric | Formula | Grain | Source fields | Caveat |
|---|---|---|---|---|---|
| 1 | Recall events | count of distinct `event_id` in period | event | `event_id`, `report_month` | Default count everywhere. Not a rate; no production denominator. |
| 2 | Recall products | count of `recall_number` in period | product | `recall_number` | Inflated by multi-SKU recalls (mean ~3.8 products/event); shown only as context. |
| 3 | Monthly events by category | events with `category_id = k` in month m (zeros filled) | event x month x category | `report_month`, `category_id` | Category is the *stated reason* from the classifier; Unclassified kept as its own series. |
| 4 | Category share | events in category k / all classified events in month m | event | as #3 | Basis of p-charts; removes overall volume swings driven by FDA posting cadence. |
| 5 | Class I share | events with `classification = Class I` / all events in period | event | `classification` (event = most severe product class) | Food ~44% vs drug ~10% Class I at product level: compare within product type only. |
| 6 | Severity-weighted count | sum over events of w(class), w = 3/2/1/0 for Class I/II/III/Not Yet Classified | event | `class_severity` | Weights are ordinal and arbitrary; Class-I-only view shown as sensitivity. |
| 7 | Vital few | smallest set of categories whose cumulative share of events >= 80% | event | #1 by category | Computed per product type and period; Unclassified shown, not hidden. |
| 8 | Control limits (c-chart) | CL = mean of Phase I monthly counts c̄; UCL/LCL = c̄ +/- 3*sqrt(c̄) (Laney-adjusted if overdispersed), LCL floored at 0 | event x month | #3 | Describes stability of FDA-recorded recall activity, not firm quality. |
| 9 | Control limits (p-chart) | p̄ = Phase I pooled share; limits p̄ +/- 3*sqrt(p̄(1-p̄)/n_m) with Laney sigma-Z adjustment | event x month | #4 | n_m = classified events in month m. |
| 10 | SPC signal | rule 1: point beyond 3-sigma limit; rule 2: 8 consecutive points on one side of CL | category x month | #8/#9 | False-alarm rate measured by simulation (T4.2.2). |
| 11 | Annual rate ratio | exp(12 * beta) from Poisson/NB GLM of monthly count on month index, trailing 60 months | category | #3 | BH q-values across categories. |
| 12 | Momentum | log((events trailing 12m + 0.5) / (events prior 12m + 0.5)) | category x product type | #3 | Regression to the mean - compared against momentum-only baseline. |
| 13 | Risk score | weighted sum of within-product-type rank percentiles of momentum, Class I share (24m), SPC signals (6m), breadth, log volume; weights 0.35/0.25/0.20/0.10/0.10 | category x product type x month | #5, #10, #12 | Pre-registered in T5.1.1; transparent, not a probability. |
| 14 | Classifier macro-F1 | mean of per-class F1 over taxonomy classes, out-of-fold, GroupKFold by firm | gold events | gold labels vs predictions | Gold set is not prevalence-representative. |
| 15 | Reporting lag | `report_date` - `recall_initiation_date` in days | product | dates | Measured: P90 160 days (all types). |

## Date field
Month = `report_date` (see `dmaic-framing.md`). Sensitivity: `recall_initiation_date` with last 6 months truncated.
