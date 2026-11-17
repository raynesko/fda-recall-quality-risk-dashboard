import math

import pandas as pd
import pytest

from fda_recall.risk.score import WEIGHTS, raw_components, score_at

START = pd.Timestamp("2020-01-01")
T = pd.Timestamp("2021-12-01")


def ev(rows):
    return pd.DataFrame(rows, columns=["event_id", "product_type", "category", "report_month",
                                       "classification", "firm_norm"])


def toy():
    r = []
    i = 0

    def add(cat, month, cls="Class II", firm="f9"):
        nonlocal i
        i += 1
        r.append([str(i), "Food", cat, pd.Timestamp(month), cls, firm])
    # A: P12 = 1 (2020), T12 = 4 (2021); 2 Class I of 5 in 24m; firms f1,f1,f2,f3 in T12 -> breadth 0.5
    add("A", "2020-03-01", "Class I")
    add("A", "2021-02-01", "Class I", "f1")
    add("A", "2021-05-01", "Class II", "f1")
    add("A", "2021-08-01", "Class II", "f2")
    add("A", "2021-11-01", "Class II", "f3")
    # B: P12 = 2, T12 = 1; no Class I; one firm -> breadth 0
    add("B", "2020-04-01")
    add("B", "2020-09-01")
    add("B", "2021-06-01", firm="f5")
    return ev(r)


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0, abs=1e-12)


def test_toy_score_matches_hand_calculation():
    s = score_at(toy(), T, START).set_index("category")
    assert s.loc["A", "momentum"] == pytest.approx(math.log(4.5 / 1.5))
    assert s.loc["A", "severity"] == pytest.approx(0.4) and s.loc["A", "breadth"] == pytest.approx(0.5)
    assert (s["signal"] == 0).all()  # < 24 months of Phase I -> 0
    # pct: A wins every component except signal (tie 0.75): .35+.25+.2*.75+.1+.1
    assert s.loc["A", "score"] == pytest.approx(0.95, abs=1e-9)
    assert s.loc["B", "score"] == pytest.approx(0.55, abs=1e-9)
    assert s.loc["A", "top_component"] == "momentum"


def test_min_volume_guard_suppresses_flag():
    s = score_at(toy(), T, START).set_index("category")
    assert not s.loc["A", "flag"]  # top quartile and rising, but T12 = 4 < 10
    s2 = score_at(toy(), T, START, min_volume=3).set_index("category")
    assert s2.loc["A", "flag"] and not s2.loc["B", "flag"]


def test_leakage_rows_after_origin_do_not_change_score():
    full = toy()
    later = ev([["99", "Food", "B", pd.Timestamp("2022-03-01"), "Class I", "f7"],
                ["98", "Food", "A", pd.Timestamp("2022-01-01"), "Class I", "f7"]])
    a = raw_components(pd.concat([full, later]), T, START)
    b = raw_components(full, T, START)
    pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True))
