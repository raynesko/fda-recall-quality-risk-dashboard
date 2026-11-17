import numpy as np
from statsmodels.stats.multitest import multipletests

from fda_recall.analysis.trend import bh, fit_trend


def test_recovers_known_20pct_growth():
    rng = np.random.default_rng(42)
    years = np.arange(60) / 12
    mu = 20 * 1.20 ** years
    r = fit_trend(rng.poisson(mu), years)
    assert r["ci_low"] < 1.20 < r["ci_high"]
    assert r["model_used"] == "poisson"


def test_overdispersed_switches_to_negative_binomial():
    rng = np.random.default_rng(1)
    years = np.arange(60) / 12
    y = rng.negative_binomial(n=2, p=2 / (2 + 15), size=60)  # mean 15, strong overdispersion
    r = fit_trend(y, years)
    assert r["dispersion"] > 1.5 and r["model_used"] == "negative_binomial"


def test_bh_matches_statsmodels():
    p = np.array([0.001, 0.04, 0.03, 0.2, 0.5, 0.012, 0.9])
    assert np.allclose(bh(p), multipletests(p, method="fdr_bh")[1], atol=1e-12)
