"""Trend tests per category (T4.2.3).

    python -m fda_recall.analysis.trend

Poisson GLM of monthly event counts on time (years) over the trailing 60 complete months, per
product_type x category. If Pearson dispersion (chi2 / df_resid) > 1.5, refit as negative binomial (NB2,
alpha estimated by maximum likelihood). Annual rate ratio = exp(beta_year). Benjamini-Hochberg q-values
across all tested series. Series with < 20 events in the window are not tested (listed as such).
Counts, not rates: a rate ratio here is the ratio of monthly EVENT counts one year apart.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial

from ..metrics import record_metric

ROOT = Path(__file__).resolve().parents[3]
SERIES = ROOT / "data" / "processed" / "series_monthly.parquet"
TABLE = ROOT / "reports" / "tables" / "trend_tests.csv"
SRC = "analysis/trend.py"
WINDOW = 60
MIN_EVENTS = 20
DISP_SWITCH = 1.5
UNCL = "UNCLASSIFIED"


def bh(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (q-values)."""
    p = np.asarray(p, float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(q, 1.0)
    return out


def fit_trend(y: np.ndarray, years: np.ndarray) -> dict:
    X = sm.add_constant(np.asarray(years, float))
    pois = sm.GLM(np.asarray(y, float), X, family=sm.families.Poisson()).fit()
    disp = float(pois.pearson_chi2 / pois.df_resid)
    if disp > DISP_SWITCH:
        nb = NegativeBinomial(np.asarray(y, float), X, loglike_method="nb2").fit(disp=0, maxiter=200)
        b, se, p, used = nb.params[1], nb.bse[1], nb.pvalues[1], "negative_binomial"
    else:
        b, se, p, used = pois.params[1], pois.bse[1], pois.pvalues[1], "poisson"
    return {"annual_rate_ratio": float(np.exp(b)), "ci_low": float(np.exp(b - 1.96 * se)),
            "ci_high": float(np.exp(b + 1.96 * se)), "p": float(p), "dispersion": disp, "model_used": used}


def main() -> int:
    g = pd.read_parquet(SERIES)
    end = g["month"].max()
    start = end - pd.DateOffset(months=WINDOW - 1)
    w = g[(g["month"] >= start) & (g["category"] != UNCL)]
    rows = []
    for (pt, cat), s in w.groupby(["product_type", "category"]):
        s = s.sort_values("month")
        n = int(s["n_events"].sum())
        base = {"product_type": pt, "category": cat, "n_events": n, "window": f"{start:%Y-%m}..{end:%Y-%m}"}
        if n < MIN_EVENTS:
            rows.append({**base, "model_used": "not_tested_low_count"})
            continue
        years = ((s["month"] - start).dt.days / 365.25).to_numpy()
        rows.append({**base, **fit_trend(s["n_events"].to_numpy(), years)})
    t = pd.DataFrame(rows)
    tested = t["p"].notna()
    t.loc[tested, "q"] = bh(t.loc[tested, "p"].to_numpy())
    cols = ["product_type", "category", "n_events", "annual_rate_ratio", "ci_low", "ci_high", "p", "q",
            "dispersion", "model_used", "window"]
    t = t[cols].sort_values(["product_type", "q"], na_position="last")
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(TABLE, index=False)
    sig = t[t["q"] < 0.05]
    record_metric("trend.n_tested", int(tested.sum()), SRC, note=f"window {start:%Y-%m}..{end:%Y-%m}")
    record_metric("trend.n_significant_q05", int(len(sig)), SRC,
                  note="; ".join(f"{r.product_type}/{r.category} RR {r.annual_rate_ratio:.2f}" for r in sig.itertuples()))
    record_metric("trend.n_negative_binomial", int((t.model_used == "negative_binomial").sum()), SRC)
    print(t.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
