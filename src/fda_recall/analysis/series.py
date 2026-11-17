"""Monthly category time series (T4.2.1).

    python -m fda_recall.analysis.series

Primary series: month of report_date. The first month of the data (2012-06; openFDA enforcement data
starts 2012-06-20) and the latest month (partial) are both excluded as incomplete.
Sensitivity series: month of recall_initiation_date, same start, with the last N complete months truncated
because recent initiations are not yet reported. N = ceil(data.lag_p90_days / 30.4375) from metrics.json.
Grid: every month x product_type x category (incl. UNCLASSIFIED), zeros filled.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from ..metrics import DEFAULT_PATH, record_metric

ROOT = Path(__file__).resolve().parents[3]
CLASSIFIED = ROOT / "data" / "processed" / "events_classified.parquet"
EVENTS = ROOT / "data" / "processed" / "recalls_event.parquet"
OUT = ROOT / "data" / "processed" / "series_monthly.parquet"
OUT_ALT = ROOT / "data" / "processed" / "series_monthly_initiation.parquet"
SRC = "analysis/series.py"
KEYS = ["product_type", "category", "month"]


def build_grid(df: pd.DataFrame, month_col: str, start: pd.Timestamp, end: pd.Timestamp,
               categories: list[str], product_types: list[str]) -> pd.DataFrame:
    """Count events per month x product_type x category for months in [start, end]; zero-filled."""
    d = df[(df[month_col] >= start) & (df[month_col] <= end)].copy()
    d["month"] = d[month_col]
    d["is_class1"] = d["classification"].eq("Class I")
    agg = d.groupby(KEYS).agg(n_events=("event_id", "size"), n_class1=("is_class1", "sum"))
    full = pd.MultiIndex.from_product(
        [product_types, categories, pd.date_range(start, end, freq="MS")], names=KEYS)
    g = agg.reindex(full, fill_value=0).reset_index()
    g[["n_events", "n_class1"]] = g[["n_events", "n_class1"]].astype(int)
    g["month_total"] = g.groupby(["product_type", "month"])["n_events"].transform("sum")
    g["share"] = (g["n_events"] / g["month_total"]).where(g["month_total"] > 0, 0.0)
    return g


def truncation_months(lag_p90_days: float) -> int:
    return math.ceil(lag_p90_days / 30.4375)


def main() -> int:
    c = pd.read_parquet(CLASSIFIED)
    ev = pd.read_parquet(EVENTS, columns=["event_id", "recall_initiation_date"])
    c = c.merge(ev, on="event_id", how="left", validate="one_to_one")
    c["initiation_month"] = c["recall_initiation_date"].dt.to_period("M").dt.to_timestamp()

    cats = sorted(c["category"].unique())
    pts = sorted(c["product_type"].unique())
    first, last = c["report_month"].min(), c["report_month"].max()
    start, end = first + pd.DateOffset(months=1), last - pd.DateOffset(months=1)

    g = build_grid(c, "report_month", start, end, cats, pts)
    n_expected = int(((c.report_month >= start) & (c.report_month <= end)).sum())
    assert g["n_events"].sum() == n_expected
    g.to_parquet(OUT, index=False)

    lag = json.loads(Path(DEFAULT_PATH).read_text(encoding="utf-8"))["data.lag_p90_days"]["value"]
    n_trunc = truncation_months(lag)
    alt_end = end - pd.DateOffset(months=n_trunc)
    ga = build_grid(c, "initiation_month", start, alt_end, cats, pts)
    ga.to_parquet(OUT_ALT, index=False)

    record_metric("series.month_start", f"{start:%Y-%m}", SRC)
    record_metric("series.month_end", f"{end:%Y-%m}", SRC, note="latest partial month excluded")
    record_metric("series.n_months", int(g["month"].nunique()), SRC)
    record_metric("series.n_events_in_window", n_expected, SRC,
                  note=f"excludes first partial month {first:%Y-%m} and latest partial month {last:%Y-%m}")
    record_metric("series.initiation_truncation_months", n_trunc, SRC,
                  note=f"ceil(data.lag_p90_days={lag} / 30.4375); alt series ends {alt_end:%Y-%m}")
    record_metric("series.n_events_initiation_window", int(ga["n_events"].sum()), SRC)
    print({"months": g.month.nunique(), "events": n_expected, "trunc": n_trunc,
           "alt_events": int(ga.n_events.sum()), "rows": len(g)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
