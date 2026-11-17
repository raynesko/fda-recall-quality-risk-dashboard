# Quality-Risk Score: Definition and Pre-Registration (T5.1.1)

**Purpose:** rank product_type × root-cause category units by how much attention their *recent FDA-recorded recall activity* deserves from a QA intelligence function. The score is a transparent monitoring heuristic. It does not predict individual recalls and does not assess any firm.

## Unit and timing
- **Unit:** product_type (Drugs, Food) × category: 13 rule categories. UNCLASSIFIED is excluded; OTHER is never assigned by the rules.
- **Score month t:** uses only events with `report_month ≤ t`, where `t` is a complete month. The leakage test in `tests/test_risk_score.py` asserts this.
- **Counts:** recall events (event grain), keyword-rules v1 categories from `data/processed/events_classified.parquet`.

## Components
Each component is converted to a **rank percentile within product_type at month t**: pandas `rank(pct=True, method="average")`, so it lies in (0, 1].

| Component | Raw formula (month t) | Weight | Why this weight |
|---|---|---|---|
| **momentum** | log((T12 + 0.5) / (P12 + 0.5)). T12 = events in months t−11..t; P12 = events in t−23..t−12; 0.5 pseudo-count | **0.35** | The core question is "what is rising". It gets the largest single weight, but under half, so it never decides a flag alone. |
| **severity** | Class I events / all events in t−23..t; 0 if no events | **0.25** | Class I means a reasonable probability of serious harm. Severity matters to QA independently of trend. |
| **signal** | number of p-chart R1/R2 signals in months t−5..t. Limits are fitted on Phase I = the up to 60 complete months ending at t−6 (minimum 24; otherwise signal = 0), with the same code as `analysis/spc.py` | **0.20** | Statistical evidence that the category's share departed from its own recent baseline. Partly redundant with momentum, so it gets less weight. |
| **breadth** | 1 − (largest single firm's events / all events in t−11..t); 0 if no events | **0.10** | Penalizes increases driven by one firm's multi-product recall, which says little about an industry-wide failure mode. Low weight because breadth is a qualifier, not a risk. |
| **volume** | log(1 + T12) | **0.10** | Larger categories matter more in absolute terms. Low weight, because volume alone is baseline B1. |

Weights sum to 1.0 (tested). They were chosen **a priori**, before any backtest, from the reasoning above. They are not tuned. Sensitivity to them is tested in T5.1.3 (Dirichlet draws).

**score** = Σ wₖ · pctₖ, in (0, 1]. **top_component** = argmaxₖ wₖ · pctₖ, the component contributing most to that row's score.

## Flag rule
A unit is **flagged** at month t when all three conditions hold:
1. score is in the top quartile of its product_type at month t (score ≥ the 75th percentile of that product type's 13 units);
2. momentum > 0 (T12 > P12);
3. T12 ≥ 10 events (minimum-volume guard; tested on a small-count case).

## Pre-registration (dated 2026-11-16, written before T5.1.2 code exists)
This section is fixed. The file's SHA-256 is recorded in `results/metrics.json` as `risk.preregistration_sha256` before the backtest runs. Any later change to this file shows up as a hash mismatch, which the backtest checks and reports. Git is not yet initialized in this repo, so the hash plus timestamp stands in for a commit; commit this file before T5.1.2 when the repo is created.

**Origins**
- Descriptive: every 6 months, from 2016-06 to the latest complete month minus 12.
- **Inference:** the 12-month-spaced subset 2016-06, 2017-06, … (non-overlapping outcome windows).

**Eligible units at an origin:** units with T12 ≥ 10 at that origin. This is the same guard as the flag, and is decided with origin-time data only.

**Outcome**
- Primary: Δ = log((N₊₁₂ + 0.5) / (T12 + 0.5)), where N₊₁₂ = events in months t+1..t+12.
- Secondary: change in Class I share, (t+1..t+12) minus (t−11..t), reported descriptively only.

**Statistics**
1. **Spearman ρ** between score and Δ, pooled over eligible units × inference origins. 95% CI by block bootstrap that resamples origins (= years), 2,000 resamples, seed 42.
2. **precision@3:** per origin × product type, take the 3 eligible units with the highest score. A hit is a unit whose Δ is among the top 3 Δ of eligible units. Precision@3 is averaged over origin × product type cells.
   - Cells with < 6 eligible units are dropped and counted. With so few units, top-3 is near-random.
3. **Baselines**, with the same eligibility and cells:
   - B1: top 3 by T12 volume.
   - B2: top 3 by momentum.
   - B3: random 3. Its exact expectation is reported, plus a permutation test of the score (1,000 within-cell shuffles, seed 42; one-sided p).
4. **Score vs B1 and score vs B2:** paired difference in precision@3 per cell, sign-flip permutation p-value (10,000, seed 42, one-sided), and block-bootstrap 95% CI over origins.
5. **Regression to the mean:** B2 (momentum) is expected to do *badly*, possibly below random, because categories that just rose tend to fall back. ρ between momentum and Δ is reported to show this directly.

**Success criteria (targets, not results)**
- precision@3(score) ≥ max(B1, B2, B3) + 0.15, **and**
- the 95% CI of ρ excludes 0 on the positive side.

If either criterion fails, `reports/backtest.md` states "target missed". The resume framing then becomes "monitoring framework evaluated against 3 naive baselines" with no predictive claim, and the weights are **not** re-tuned to pass.

**Reporting:** the number of origins and eligible units is printed next to every statistic. All values are written via `record_metric(..., label="achieved")`.
