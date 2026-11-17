"""Dashboard-ready tables for Power BI (SE6) + expected values for reconciliation.

    python -m fda_recall.dashboard   -> data/processed/dashboard/*.csv, docs/dashboard/reconciliation.md

All logic lives here (Python), so Power BI visuals only display precomputed columns. That keeps the
dashboard reconcilable: each page's headline numbers are listed with their expected value.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .actions import DISCLAIMER

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
OUT = PROC / "dashboard"
TABLES = ROOT / "reports" / "tables"
RECON = ROOT / "docs" / "dashboard" / "reconciliation.md"
METRICS = ROOT / "results" / "metrics.json"
FOOTER = "openFDA data - not for clinical or regulatory decisions. Counts are recall events, not rates."
RULE_TEXT = {"R1": "R1: point beyond a control limit", "R2": "R2: 8 months in a row on one side of the centre line",
             "R1+R2": "R1 + R2: beyond a limit and part of an 8-month run"}
TOOLTIP = ("Common-cause variation = normal month-to-month noise inside the limits. A red point is a "
           "special-cause signal: this month's share is unusual compared with the 2015-2019 baseline. "
           "It is a prompt to look, not proof of a quality problem.")
COMPONENT_TEXT = {"momentum": "rising recall count", "severity": "high Class I share", "signal": "recent SPC signals",
                  "breadth": "spread across many firms", "volume": "large volume"}


def save(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    df.to_parquet(OUT / f"{name}.parquet", index=False)  # typed source for the Power BI project


def why_flagged(r) -> str:
    pct = f"{(r.t12 - r.p12) / r.p12:+.0%}" if r.p12 else "new"
    firm_share = 1 - r.breadth
    parts = [f"{int(r.t12)} events in the last 12 months vs {int(r.p12)} before ({pct})",
             f"{r.severity:.0%} Class I (24 m)",
             f"{int(r.signal)} SPC signal(s) in last 6 m",
             f"largest single firm {firm_share:.0%} of events"]
    head = f"Main driver: {COMPONENT_TEXT[r.top_component]}. "
    return head + "; ".join(parts) + "."


def build() -> dict[str, pd.DataFrame]:
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    cls = pd.read_parquet(PROC / "events_classified.parquet")
    as_of = pd.Timestamp(m["series.month_end"]["value"] + "-01")
    data_as_of = m["data.report_date_max"]["value"]

    # KPI (page 1): trailing 12 complete months vs prior 12
    t_lo, p_lo = as_of - pd.DateOffset(months=11), as_of - pd.DateOffset(months=23)
    risk = pd.read_parquet(PROC / "risk_scores.parquet")
    latest = risk[risk.month == as_of]
    rows = []
    for pt in ("All", "Drugs", "Food"):
        d = cls if pt == "All" else cls[cls.product_type == pt]
        t12 = d[(d.report_month >= t_lo) & (d.report_month <= as_of)]
        p12 = d[(d.report_month >= p_lo) & (d.report_month < t_lo)]
        fl = latest if pt == "All" else latest[latest.product_type == pt]
        rows.append({"product_type": pt, "events_trailing_12m": len(t12), "events_prior_12m": len(p12),
                     "change_pct": round((len(t12) - len(p12)) / len(p12), 4),
                     "class1_share_trailing_12m": round((t12.classification == "Class I").mean(), 4),
                     "flagged_categories": int(fl.flag.sum()), "window": f"{t_lo:%Y-%m}..{as_of:%Y-%m}",
                     "data_as_of": data_as_of, "footer": FOOTER})
    kpi = pd.DataFrame(rows)

    # monthly trend (page 1)
    s = pd.read_parquet(PROC / "series_monthly.parquet")
    monthly = (s.groupby(["product_type", "month"]).agg(events=("n_events", "sum"), class1=("n_class1", "sum"))
               .reset_index())

    # Pareto (page 2)
    par = pd.read_csv(TABLES / "pareto.csv")
    par = par[par.weight.isin(["count", "severity", "class1"])].copy()
    par["sort_order"] = par.groupby(["product_type", "period", "weight"]).cumcount() + 1
    par["bar_label"] = par["category"].where(par["category"] != "UNCLASSIFIED", "UNCLASSIFIED (no rule matched)")
    par["vital_few_label"] = par["vital_few"].map({True: "Vital few (to 80%)", False: "Other"})
    par.loc[par.category == "UNCLASSIFIED", "vital_few_label"] = "Unclassified"
    par["cum_pct"] = (par["cum_share"] * 100).round(1)
    par["period_key"] = par["period"].str.split(" ").str[0]

    # SPC (page 3)
    spc = pd.read_parquet(PROC / "spc_signals.parquet")
    spc = spc[spc.monitored].copy()
    spc["signal_label"] = spc["rule_id"].map(RULE_TEXT).fillna("")
    spc["signal_value"] = spc["value"].where(spc["signal"])
    spc["chart_label"] = spc["chart"].map({"c": "Count (c-chart)", "p": "Share of month (p-chart)"})
    spc["series"] = spc["product_type"] + " - " + spc["category"]
    spc["tooltip"] = TOOLTIP

    # Watchlist (page 4)
    stab = pd.read_csv(TABLES / "flag_stability.csv")
    w = latest.merge(stab[["product_type", "category"] + [c for c in stab.columns if c.startswith("flag_pct_")]],
                     on=["product_type", "category"], how="left")
    w["stability_pct"] = w[[c for c in w.columns if c.startswith("flag_pct_")]].min(axis=1)
    w["stability_note"] = w.apply(
        lambda r: ("Fragile: flag drops out under some assumptions" if r.flag and r.stability_pct < 60
                   else ("Robust across sensitivity runs" if r.flag else "")), axis=1)
    w["why_flagged"] = w.apply(lambda r: why_flagged(r) if r.flag else "", axis=1)
    w["rank"] = w.groupby("product_type")["score"].rank(ascending=False, method="min").astype(int)
    w["flag_label"] = w["flag"].map({True: "FLAGGED", False: ""})
    keep = ["product_type", "category", "rank", "score", "flag", "flag_label", "top_component", "why_flagged",
            "stability_pct", "stability_note", "t12", "p12", "momentum", "severity", "signal", "breadth", "volume",
            "pct_momentum", "pct_severity", "pct_signal", "pct_breadth", "pct_volume", "month"]
    watch = w[keep].sort_values(["product_type", "rank"])
    comp = watch.melt(id_vars=["product_type", "category"],
                      value_vars=["pct_momentum", "pct_severity", "pct_signal", "pct_breadth", "pct_volume"],
                      var_name="component", value_name="percentile")
    weights = {"pct_momentum": 0.35, "pct_severity": 0.25, "pct_signal": 0.20, "pct_breadth": 0.10, "pct_volume": 0.10}
    comp["weighted_contribution"] = comp.apply(lambda r: r.percentile * weights[r.component], axis=1)
    comp["component"] = comp["component"].str.replace("pct_", "", regex=False)

    actions = pd.read_csv(ROOT / "data" / "reference" / "qa_action_library.csv", encoding="utf-8-sig")
    actions["phase_order"] = actions["phase"].map({"Define": 1, "Measure": 2, "Analyze": 3, "Improve": 4, "Control": 5})
    notes = pd.DataFrame({"key": ["footer", "disclaimer_actions", "spc_tooltip", "limitations"],
                          "text": [FOOTER, DISCLAIMER, TOOLTIP,
                                   "Counts are FDA-recorded recall events with no production denominator, so they are not "
                                   "failure rates. FDA classification and enforcement priorities shape what is recorded. "
                                   "Categories come from keyword rules (~0.90 precision on accepted predictions; "
                                   "Unclassified shown). The risk score did NOT beat naive baselines in a pre-registered "
                                   "backtest: use it for triage, not prediction. USDA-FSIS meat/poultry recalls excluded."]})
    dim_pt = pd.DataFrame({"product_type": ["Drugs", "Food"]})
    return {"dim_product_type": dim_pt, "dash_kpi": kpi, "dash_monthly": monthly, "dash_pareto": par, "dash_spc": spc,
            "dash_watchlist": watch, "dash_watch_components": comp, "dash_actions": actions, "dash_notes": notes}


def reconciliation(t: dict[str, pd.DataFrame]) -> str:
    k = t["dash_kpi"].set_index("product_type")
    par = t["dash_pareto"]
    spc = t["dash_spc"]
    w = t["dash_watchlist"]
    full = par[(par.weight == "count") & par.period.str.startswith("full")]
    checks = [
        ("1 Exec", "Card: events trailing 12 m (All)", int(k.loc["All", "events_trailing_12m"]), "dash_kpi.events_trailing_12m, product_type=All"),
        ("1 Exec", "Card: events trailing 12 m (Drugs)", int(k.loc["Drugs", "events_trailing_12m"]), "slicer product_type=Drugs"),
        ("1 Exec", "Card: % Class I trailing 12 m (All)", f"{k.loc['All', 'class1_share_trailing_12m']:.1%}", "dash_kpi.class1_share_trailing_12m"),
        ("1 Exec", "Card: change vs prior 12 m (All)", f"{k.loc['All', 'change_pct']:+.1%}", "dash_kpi.change_pct"),
        ("1 Exec", "Card: flagged categories (All)", int(k.loc["All", "flagged_categories"]), "dash_kpi.flagged_categories"),
        ("1 Exec", "Total events in star schema", int(len(pd.read_parquet(PROC / "star" / "fact_recall_event.parquet"))), "COUNTROWS(fact_recall_event)"),
        ("2 Pareto", "Drugs full-period top bar", f"{full[full.product_type == 'Drugs'].iloc[0].category} = {int(full[full.product_type == 'Drugs'].iloc[0].value)}", "dash_pareto count/full"),
        ("2 Pareto", "Food full-period top bar", f"{full[full.product_type == 'Food'].iloc[0].category} = {int(full[full.product_type == 'Food'].iloc[0].value)}", "dash_pareto count/full"),
        ("2 Pareto", "Food Unclassified bar", int(full[(full.product_type == 'Food') & (full.category == 'UNCLASSIFIED')].value.iloc[0]), "dash_pareto count/full"),
        ("3 SPC", "p-chart Phase II signals (all monitored)", int(spc[(spc.chart == 'p') & (spc.phase == 'II')].signal.sum()), "metrics spc.n_signals"),
        ("3 SPC", "c-chart Phase II signals (all monitored)", int(spc[(spc.chart == 'c') & (spc.phase == 'II')].signal.sum()), "metrics spc.c.phase2_signal_months"),
        ("4 Watchlist", "Flagged rows", int(w.flag.sum()), "metrics risk.latest_n_flagged"),
    ]
    for r in w[w.flag].itertuples():
        checks.append(("4 Watchlist", f"Score {r.product_type}/{r.category}", f"{r.score:.3f}", "dash_watchlist.score"))
    L = ["# Dashboard Reconciliation (expected values generated by `python -m fda_recall.dashboard`)", "",
         "Fill the *Dashboard value* column while testing in Power BI. Pass = identical value. "
         "Target: >= 5 checks, zero difference.", "",
         "| Page | Check | Expected (Python) | Source | Dashboard value | Pass |", "|---|---|---|---|---|---|"]
    L += [f"| {p} | {c} | {v} | {s} |  |  |" for p, c, v, s in checks]
    return "\n".join(L) + "\n"


def main() -> int:
    t = build()
    for name, df in t.items():
        save(df, name)
    RECON.parent.mkdir(parents=True, exist_ok=True)
    RECON.write_text(reconciliation(t), encoding="utf-8")
    print({k: len(v) for k, v in t.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
