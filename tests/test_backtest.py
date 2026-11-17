import numpy as np
import pandas as pd
import pytest

from fda_recall.risk.backtest import sign_flip_p, topk_hits


def test_topk_hits_known_answer():
    idx = list("abcdef")
    delta = pd.Series([6, 5, 4, 3, 2, 1], index=idx, dtype=float)  # top3 = a,b,c
    assert topk_hits(pd.Series([9, 8, 7, 0, 0, 0], index=idx, dtype=float), delta) == pytest.approx(1.0)
    assert topk_hits(pd.Series([0, 0, 9, 8, 7, 0], index=idx, dtype=float), delta) == pytest.approx(1 / 3)
    assert topk_hits(pd.Series([0, 0, 0, 9, 8, 7], index=idx, dtype=float), delta) == pytest.approx(0.0)


def test_sign_flip_p_extremes():
    assert sign_flip_p(np.ones(12), n=2000) < 0.01
    assert sign_flip_p(-np.ones(12), n=2000) > 0.99
