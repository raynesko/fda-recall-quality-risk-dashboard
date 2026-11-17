"""Transparent quality-risk score (T5.1.1). Definition: docs/methodology/risk-score.md (pre-registered).

    python -m fda_recall.risk.score       -> data/processed/risk_scores.parquet

Every function that scores month t first drops events with report_month > t (leakage-safe by construction).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..analysis import spc
from ..analysis.series import build_grid
from ..metrics import record_metric

ROOT = Path(__file__).resolve().parents[3]
CLASSIFIED = ROOT / "data" / "processed" / "events_classified.parquet"
EVENTS = ROOT / "data" / "processed" / "recalls_event.parquet"
OUT = ROOT / "data" / "processed" / "risk_scores.parquet"
SRC = "risk/score.py"
UNCL = "UNCLASSIFIED"
WEIGHTS = {"momentum": 0.35, "severity": 0.25, "signal": 0.20, "breadth": 0.10, "volume": 0.10}
PSEUDO = 0.5
MIN_VOLUME = 10
PHASE1_MAX, PHASE1_MIN, SIGNAL_WINDOW = 60, 24, 6


def load_events() -> pd.DataFrame:
    c = pd.read_parquet(CLASSIFIED)
    f = pd.read_parquet(EVENTS, columns=["event_id", "firm_norm"])
    return c.merge(f, on="event_id", how="left", validate="one_to_one")


def months_back(t: pd.Timestamp, k: int) -> pd.Timestamp:
    return t - pd.DateOffset(months=k)


def signal_count(s: pd.DataFrame, t: pd.Timestamp, start: pd.Timestamp) -> int:
    """p-chart signals in t-5..t with Phase I = up to 60 complete months ending at t-6 (min 24)."""
    p1_end = months_back(t, SIGNAL_WINDOW)
    p1_start = max(start, months_back(p1_end, PHASE1_MAX - 1))
    in_base = s["month"].between(p1_start, p1_end).to_numpy()
    if in_base.sum() < PHASE1_MIN:
        return 0
    x, n = s["n_events"].to_numpy(float), s["month_total"].to_numpy(float)
    pbar = x[in_base].sum() / n[in_base].sum() if n[in_base].sum() > 0 else 0.0
    if pbar <= 0 or pbar >= 1:
        return 0
    share = np.where(n > 0, x / np.where(n > 0, n, 1), 0.0)
    res = spc.chart(share, in_base, "p", n)
    recent = (s["month"] > p1_end).to_numpy()
    return int((res["r1"] | res["r2"])[recent].sum())


def raw_components(ev: pd.DataFrame, t: pd.Timestamp, start: pd.Timestamp, window: int = 12) -> pd.DataFrame:
    """window: trailing months for momentum/volume/breadth (default 12; T5.1.3 tests 6 and 24).
    Columns keep the names t12/p12 for the trailing and prior window counts."""
    e = ev[ev["report_month"] <= t]  # leakage guard
    cats = sorted(set(ev["category"]))
    pts = sorted(set(ev["product_type"]))
    g = build_grid(e, "report_month", start, t, cats, pts)
    rows = []
    t12_lo, p12_lo, s24_lo = months_back(t, window - 1), months_back(t, 2 * window - 1), months_back(t, 23)
    win12 = e[e["report_month"] >= t12_lo]
    top_firm = (win12.groupby(["product_type", "category", "firm_norm"]).size()
                .groupby(level=[0, 1]).max())
    for (pt, cat), s in g.groupby(["product_type", "category"]):
        if cat == UNCL:
            continue
        s = s.sort_values("month")
        m = s["month"]
        t12 = int(s.loc[m >= t12_lo, "n_events"].sum())
        p12 = int(s.loc[(m >= p12_lo) & (m < t12_lo), "n_events"].sum())
        n24 = int(s.loc[m >= s24_lo, "n_events"].sum())
        c24 = int(s.loc[m >= s24_lo, "n_class1"].sum())
        tf = int(top_firm.get((pt, cat), 0))
        rows.append({"product_type": pt, "category": cat, "month": t, "t12": t12, "p12": p12,
                     "momentum": float(np.log((t12 + PSEUDO) / (p12 + PSEUDO))),
                     "severity": c24 / n24 if n24 else 0.0,
                     "signal": signal_count(s, t, start),
                     "breadth": 1 - tf / t12 if t12 else 0.0,
                     "volume": float(np.log1p(t12))})
    return pd.DataFrame(rows)


def score_frame(raw: pd.DataFrame, weights: dict[str, float] = WEIGHTS,
                min_volume: int = MIN_VOLUME) -> pd.DataFrame:
    """Rank-percentile components within product_type x month, weighted sum, top component, flag."""
    d = raw.copy()
    grp = d.groupby(["product_type", "month"])
    contrib = pd.DataFrame(index=d.index)
    for k, w in weights.items():
        d[f"pct_{k}"] = grp[k].rank(pct=True, method="average")
        contrib[k] = w * d[f"pct_{k}"]
    d["score"] = contrib.sum(axis=1)
    d["top_component"] = contrib.idxmax(axis=1)
    q75 = d.groupby(["product_type", "month"])["score"].transform(lambda s: s.quantile(0.75))
    d["flag"] = (d["score"] >= q75) & (d["momentum"] > 0) & (d["t12"] >= min_volume)
    return d


def score_at(ev: pd.DataFrame, t: pd.Timestamp, start: pd.Timestamp, **kw) -> pd.DataFrame:
    return score_frame(raw_components(ev, t, start), **kw)


def score_months(ev: pd.DataFrame, months, start: pd.Timestamp, **kw) -> pd.DataFrame:
    raw = pd.concat([raw_components(ev, t, start) for t in months], ignore_index=True)
    return score_frame(raw, **kw)


def main() -> int:
    ev = load_events()
    first, last = ev["report_month"].min(), ev["report_month"].max()
    start, end = first + pd.DateOffset(months=1), last - pd.DateOffset(months=1)  # complete months only
    months = pd.date_range(months_back(start, -23), end, freq="MS")  # need 24 months of history
    sc = score_months(ev, months, start)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sc.to_parquet(OUT, index=False)
    latest = sc[sc.month == end]
    record_metric("risk.score_months", f"{months[0]:%Y-%m}..{end:%Y-%m}", SRC)
    record_metric("risk.latest_month", f"{end:%Y-%m}", SRC)
    record_metric("risk.latest_n_flagged", int(latest.flag.sum()), SRC,
                  note="; ".join(f"{r.product_type}/{r.category}" for r in latest[latest.flag].itertuples()))
    print(latest.sort_values(["product_type", "score"], ascending=[True, False])
          [["product_type", "category", "t12", "p12", "momentum", "severity", "signal", "breadth", "score",
            "top_component", "flag"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
