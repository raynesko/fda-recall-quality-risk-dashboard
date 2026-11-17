import pandas as pd
import pytest

from fda_recall.analysis.pareto import UNCL, pareto, tau, trailing_window, view_values


def test_pareto_toy_known_answer():
    # total 100: A 50, B 25, UNCL 15, C 10 -> ranked A, B, C then UNCL last
    t = pareto(pd.Series({"B": 25, "A": 50, UNCL: 15, "C": 10}))
    assert list(t.category) == ["A", "B", "C", UNCL]
    assert t.cum_share.tolist() == pytest.approx([0.50, 0.75, 0.85, 1.00])
    assert t.vital_few.tolist() == [True, True, True, False]  # 80% first reached at C
    assert t["rank"].iloc[-1] is pd.NA


def test_pareto_threshold_hit_exactly_and_no_unclassified():
    t = pareto(pd.Series({"A": 80, "B": 20}))
    assert t.vital_few.tolist() == [True, False]
    assert t.cum_share.iloc[-1] == pytest.approx(1.0)


def test_view_values_weights():
    df = pd.DataFrame({"category": ["A", "A", "B"], "class_severity": [3, 1, 2],
                       "classification": ["Class I", "Class III", "Class II"]})
    assert view_values(df, "count").to_dict() == {"A": 2, "B": 1}
    assert view_values(df, "severity").to_dict() == {"A": 4, "B": 2}
    assert view_values(df, "class1").to_dict() == {"A": 1}


def test_tau_identical_rankings_and_trailing_window_excludes_partial_month():
    a = pd.Series({"A": 3, "B": 2, "C": 1, UNCL: 9})
    assert tau(a, a * 2) == pytest.approx(1.0)
    months = pd.date_range("2020-01-01", "2026-11-01", freq="MS")
    sub, label = trailing_window(pd.DataFrame({"report_month": months}), 60)
    assert len(sub) == 60 and sub.report_month.max() == pd.Timestamp("2026-10-01")
    assert label == "2021-11..2026-10"
