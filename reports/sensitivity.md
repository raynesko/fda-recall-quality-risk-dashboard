# Risk-Score Sensitivity (T5.1.3)

Month scored: 2026-10. Values in `results/metrics.json` under `sens.*`; tables `reports/tables/flag_stability.csv`, `reports/tables/sensitivity_tau.csv`; figure `reports/figures/risk_rank_stability.png`.

## Median Kendall tau vs default ranking

| family      | product_type   |   tau |
|:------------|:---------------|------:|
| label_noise | Drugs          | 0.74  |
| label_noise | Food           | 0.452 |
| weights     | Drugs          | 0.718 |
| weights     | Food           | 0.735 |
| window_24m  | Drugs          | 0.256 |
| window_24m  | Food           | 0.4   |
| window_6m   | Drugs          | 0.564 |
| window_6m   | Food           | 0.468 |

Target (weights, median tau >= 0.70): **met** (0.735).

## Flag stability (% of runs flagged)

| product_type   | category           | default_flag   |   default_score |   flag_pct_label_noise |   flag_pct_weights |   flag_pct_window |
|:---------------|:-------------------|:---------------|----------------:|-----------------------:|-------------------:|------------------:|
| Drugs          | FOREIGN            | True           |           0.85  |                   98   |               88.6 |               100 |
| Drugs          | MICRO              | True           |           0.8   |                   97.5 |               71.9 |                50 |
| Drugs          | MIXUP              | True           |           0.704 |                   77.5 |               95.2 |               100 |
| Drugs          | STERILITY          | True           |           0.7   |                   82.5 |               93.6 |                50 |
| Drugs          | LABELING           | False          |           0.619 |                   25.5 |                3.4 |                 0 |
| Drugs          | POTENCY            | False          |           0.554 |                    2.5 |               16.9 |                50 |
| Drugs          | SPEC_FAIL          | False          |           0.523 |                    3   |                9.3 |                 0 |
| Drugs          | PACKAGING          | False          |           0.458 |                    0.5 |                0   |                 0 |
| Drugs          | UNAPPROVED         | False          |           0.404 |                    0.5 |                0   |                 0 |
| Drugs          | PROCESS_SANITATION | False          |           0.392 |                    0   |                0   |                 0 |
| Drugs          | IMPURITY           | False          |           0.365 |                    0   |                0   |                50 |
| Drugs          | CGMP               | False          |           0.325 |                    0   |                0   |                 0 |
| Drugs          | ALLERGEN           | False          |           0.306 |                    0   |                0   |                 0 |
| Food           | UNAPPROVED         | True           |           0.862 |                   91.5 |               82.1 |                50 |
| Food           | IMPURITY           | True           |           0.723 |                   34   |               80.1 |                 0 |
| Food           | ALLERGEN           | False          |           0.704 |                    0   |                0   |                 0 |
| Food           | PROCESS_SANITATION | True           |           0.685 |                   19   |               46.3 |                 0 |
| Food           | MICRO              | False          |           0.627 |                    0   |                0   |               100 |
| Food           | POTENCY            | False          |           0.627 |                    2   |                0   |                 0 |
| Food           | MIXUP              | False          |           0.544 |                    0.5 |                0   |                 0 |
| Food           | FOREIGN            | False          |           0.458 |                    0   |                0   |                 0 |
| Food           | LABELING           | False          |           0.446 |                    0   |                0   |                 0 |
| Food           | CGMP               | False          |           0.421 |                    0   |                0   |                 0 |
| Food           | SPEC_FAIL          | False          |           0.358 |                    1   |                0   |                 0 |
| Food           | PACKAGING          | False          |           0.327 |                    1   |                0   |                 0 |
| Food           | STERILITY          | False          |           0.219 |                    1   |                0   |                 0 |

## Fragile flags (< 60% in at least one family)

- Drugs / MICRO
- Drugs / STERILITY
- Food / UNAPPROVED
- Food / IMPURITY
- Food / PROCESS_SANITATION

Label noise rate 0.105 = 1 - precision on accepted predictions (gold set). Noise is uniform over other categories, which is harsher than real confusions (those concentrate in overlapping pairs).
