# openFDA Enforcement Source Notes (T2.1.1)

Retrieved 2026-11-15 by live queries against api.fda.gov and the bulk download service. Numbers below are observed, not assumed.

## Endpoints
| Endpoint | URL | Total records (API `meta.results.total`) | API `last_updated` |
|---|---|---|---|
| Drug enforcement | https://api.fda.gov/drug/enforcement.json | 18,110 | 2026-11-04 |
| Food enforcement | https://api.fda.gov/food/enforcement.json | 29,598 | 2026-11-04 |
| Device enforcement (out of scope) | https://api.fda.gov/device/enforcement.json | 40,481 | 2026-11-04 |

Queries used: `?limit=1` (meta + sample record); `?count=<field>.exact`; `?sort=report_date:asc|desc&limit=1`; `?search=_missing_:center_classification_date`.

## Coverage observed (from bulk files, export date 2026-11-10)
| | Drug | Food |
|---|---|---|
| Product-level rows (unique `recall_number`) | 18,110 | 29,598 |
| Distinct `event_id` | 4,740 | 7,947 |
| Rows per event (mean) | ~3.8 | ~3.7 |
| min / max `report_date` | 2012-06-20 / 2026-11-04 | 2012-06-20 / 2026-11-04 |
| min `recall_initiation_date` | 2006-02-24 | 0212-12-07 (malformed, 1 row) |

**Discrepancy:** the openFDA drug enforcement documentation says records run "from 2004 to the present" (https://open.fda.gov/apis/drug/enforcement/), but the earliest `report_date` in both endpoints is 2012-06-20. Some recalls initiated earlier (to 2006) appear, reported from 2012. Plan consequence: time series start 2012-06, so 2012 is a partial year; the 2015-2019 Phase I baseline window still fits.

Rows by `report_date` year (bulk): drug 2012 434, 2013 1377, 2014 1562, 2015 2020, 2016 1254, 2017 1073, 2018 1426, 2019 2152, 2020 1035, 2021 1016, 2022 1349, 2023 1252, 2024 657, 2025 765, 2026 (to Nov) 738. Food 2012 1917, 2013 2111, 2014 2259, 2015 2834, 2016 3011, 2017 3203, 2018 1958, 2019 1863, 2020 1286, 2021 1181, 2022 1652, 2023 2155, 2024 1409, 2025 1617, 2026 (to Nov) 1142. Counts are volatile year to year (and may be batchy by product rows per event) - SPC at event level will need care.

## Fields (confirmed present in a live sample record)
Both endpoints: `recall_number, event_id, reason_for_recall, classification, report_date, recall_initiation_date, center_classification_date, status, recalling_firm, state, city, country, product_type, voluntary_mandated, product_description, distribution_pattern, product_quantity, code_info, initial_firm_notification, address_1/2, postal_code, termination_date (when terminated), openfda`. Food also has `more_code_info`. No field identifies the FDA center (CDER vs CBER). `openfda` was an empty object in the sample drug/food records.

Dates are strings `YYYYMMDD`. Observed data quality: 0 empty `reason_for_recall`; 1 food `recall_initiation_date` malformed (`02121207`); `center_classification_date` missing for 2 drug rows and 1 food row.

## Categorical values observed (`count=<field>.exact`)
- `classification` drug: Class II 14,632; Class I 1,753; Class III 1,723; **Not Yet Classified 2**. Food: Class II 14,801; **Class I 13,003**; Class III 1,793; Not Yet Classified 1. (Food Class I share ~44%, drug ~10% - big difference to understand before severity-weighting; do not assume.)
- `voluntary_mandated` drug: Voluntary: Firm initiated 18,046; FDA Mandated 29; N/A 23; blank 12. Food: 29,195; 396; 6; 1.
- `status`: Terminated / Ongoing / Completed (drug 14,831/2,857/422; food 27,982/1,184/432).
- `product_type`: "Drugs" / "Food".
- So unclassified recalls do appear (3 rows total) - resolves the discrepancy flagged in the primer. Handle as a separate class in cleaning.

## Rate limits, paging (sources)
- Without key: 240 requests/min/IP and 1,000 requests/day/IP; with key: 240/min/key and 120,000/day/key; key via `api_key` query parameter or basic auth. Source: https://open.fda.gov/apis/authentication/
- `limit` max 1,000; `skip` max 25,000. Source: https://open.fda.gov/apis/query-parameters/. Confirmed live: `skip=30000` returned HTTP 400 "Skip value must 25000 or less."
- Food has 29,598 rows, more than 25,000 + 1,000, so plain skip paging cannot fetch everything. The API returns a `Link: rel="next"` header with a `search_after` cursor (observed in a live response header; not documented on the query-parameters page).

## Bulk download
`https://api.fda.gov/download.json` (observed) lists, with export date 2026-11-10:
- https://download.open.fda.gov/drug/enforcement/drug-enforcement-0001-of-0001.json.zip - 3.79 MB listed (3,978,128 bytes downloaded), 18,110 records
- https://download.open.fda.gov/food/enforcement/food-enforcement-0001-of-0001.json.zip - 5.60 MB listed (5,873,947 bytes downloaded), 29,598 records
Record counts match the API totals. The page https://open.fda.gov/data/downloads/ itself showed only navigation in my fetch; the manifest above is the evidence.

## Decision
**Use bulk download** (single small file per endpoint, exactly matches API totals, no paging or rate-limit issues, hashable for the manifest). Use the API only for count checks against `meta.results.total`. Re-download only on an explicit refresh and keep dated raw folders.

## Biologics, device and update cadence
- No field identifies the issuing center, so biologics cannot be separated or excluded by field. A product description in the drug file mentions a BCG vaccine (a biologic-type product, regulatory center not confirmed - UNVERIFIED), so some non-CDER products likely appear. Treat the drug endpoint as "drug-labeled enforcement records" and state that in limitations.
- Devices exist as a separate endpoint (40,481 rows) and stay out of scope.
- Update cadence: openFDA states weekly updates (https://open.fda.gov/apis/drug/enforcement/); observed API `last_updated` 2026-11-04 and bulk export 2026-11-10.

## Implications for other tickets
- T2.1.2: ingest from bulk; check row counts to API totals; no key needed.
- T2.1.3: handle malformed date `02121207`, 'Not Yet Classified', blank `voluntary_mandated`; event grain is ~4.7k drug / ~7.9k food events.
- T1.1.3 / T4.2.1: time series begins 2012-06; reconsider Phase I window length (2015-2019 = 60 months) and note the food Class I share when choosing severity weights.

Time spent: ~1.0 h equivalent (agent session; within 1.5 h box).
