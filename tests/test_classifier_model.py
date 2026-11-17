import numpy as np
import pandas as pd

from fda_recall.classify import model

TEXTS = pd.Series(["undeclared milk", "undeclared egg", "listeria found", "salmonella positive",
                   "glass pieces", "metal fragments", "undeclared soy", "listeria monocytogenes",
                   "plastic pieces", "salmonella contamination"])
Y = pd.Series(["A", "A", "M", "M", "F", "F", "A", "M", "F", "M"])
G = pd.Series(list("abcdeabcde"))


def test_deterministic_predictions():
    p1, c1 = model.oof_predict(TEXTS, Y, G)
    p2, c2 = model.oof_predict(TEXTS, Y, G)
    assert p1.tolist() == p2.tolist() and np.allclose(c1, c2)
    m = model.build_model().fit(TEXTS, Y)
    assert m.predict(["undeclared milk powder"])[0] == "A"


def test_bootstrap_identical_models_zero_diff():
    bs = model.paired_bootstrap(Y, Y, Y, sorted(Y.unique()), n=200)
    assert bs["diff_ci"] == (0.0, 0.0)


def test_mcnemar_table():
    p, t = model.mcnemar_p(["a", "b", "c"], ["a", "b", "x"], ["a", "x", "c"])
    assert t == [[1, 1], [1, 0]] and 0 <= p <= 1
