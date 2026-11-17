import pandas as pd

from fda_recall.analysis.series import build_grid, truncation_months


def toy():
    m = pd.to_datetime(["2020-01-01", "2020-01-01", "2020-03-01", "2020-04-01"])
    return pd.DataFrame({"event_id": ["1", "2", "3", "4"], "product_type": ["Food", "Drugs", "Food", "Food"],
                         "category": ["A", "B", "A", "B"], "report_month": m,
                         "classification": ["Class I", "Class II", "Class I", "Class III"]})


def test_grid_complete_zero_filled_and_sums():
    g = build_grid(toy(), "report_month", pd.Timestamp("2020-01-01"), pd.Timestamp("2020-03-01"),
                   ["A", "B"], ["Drugs", "Food"])
    assert len(g) == 2 * 2 * 3 and not g.duplicated(["product_type", "category", "month"]).any()
    assert g.n_events.sum() == 3  # April event is outside the window
    feb = g[g.month == "2020-02-01"]
    assert (feb.n_events == 0).all() and (feb.share == 0).all()
    jan_food = g[(g.month == "2020-01-01") & (g.product_type == "Food")].set_index("category")
    assert jan_food.loc["A", "n_events"] == 1 and jan_food.loc["A", "share"] == 1.0
    assert jan_food.loc["A", "n_class1"] == 1


def test_truncation_months():
    assert truncation_months(160) == 6
    assert truncation_months(30.4375) == 1
