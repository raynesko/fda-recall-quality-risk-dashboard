# Risk-Score Backtest (T5.1.2)

Pre-registered plan: `docs/methodology/risk-score.md` (hash match: **True**). All numbers are in `results/metrics.json` under `backtest.*`.

**Design:** 10 yearly origins 2016-06..2025-06, 17 origin x product cells, 161 eligible unit-origins. Origins every 12 months (non-overlapping 12-month outcome windows) for inference; 19 six-monthly origins descriptive only. Eligible unit = product_type x category with >= 10 events in the 12 months before the origin; 3 cells dropped for < 6 eligible units. Outcome = log change in events, next 12 months vs trailing 12 months. Leakage check on real data passed.

## Precision@3 (hit = unit's outcome ranks in the cell's top 3)

| method | inference (yearly) | descriptive (6-monthly) |
|---|---|---|
| score | 0.235 | 0.242 |
| B1_volume | 0.314 | 0.333 |
| B2_momentum | 0.176 | 0.212 |
| B3_random_expected | 0.382 | 0.384 |

Score permutation test (within-cell shuffles, one-sided): p = 0.9990.

- Score minus B1_volume: -0.078 per cell, sign-flip p = 0.9444, block-bootstrap 95% CI -0.204 to +0.044 (n = 17 cells).
- Score minus B2_momentum: +0.059 per cell, sign-flip p = 0.1899, block-bootstrap 95% CI -0.021 to +0.137 (n = 17 cells).

## Rank correlation

- Spearman rho(score, outcome) = -0.308, 95% CI -0.446 to -0.184 (n = 161 eligible unit-origins, 10 origins).
- Regression to the mean: rho(momentum, outcome) = -0.370, 95% CI -0.501 to -0.239. A negative value means categories that just rose tended to fall back.

## Secondary (descriptive)

Mean change in Class I share, next 12 m vs trailing 12 m: flagged units +0.008, not flagged -0.004.

## Verdict against pre-registered targets

- precision@3(score) >= best baseline (B3_random_expected, 0.382) + 0.15: **MISSED** (0.235).
- rho 95% CI excludes 0 on the positive side: **MISSED**.

**Target missed.** Per the pre-registration, weights are not re-tuned and the score is presented as a transparent monitoring/triage framework evaluated against 3 naive baselines, with no predictive claim.

Caveats: few origins and units, so every interval is wide; categories come from keyword rules with precision ~0.90 on accepted predictions (label-noise sensitivity in T5.1.3); counts reflect FDA enforcement and reporting as well as industry failures.
