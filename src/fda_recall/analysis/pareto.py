"""Pareto analysis of root-cause categories (T4.1.1).

    python -m fda_recall.analysis.pareto

Unit: recall EVENTS (not products, not rates). Categories come from keyword rules v1
(data/processed/events_classified.parquet).

Views = product_type (Drugs, Food) x period (full; trailing 60 complete months) x weight:
  count     - events
  severity  - sum of class_severity (Class I=3, II=2, III=1, Not Yet Classified=0; ordinal, arbitrary)
  class1    - Class I events only (sensitivity check on the weights)
UNCLASSIFIED is kept as its own bar, placed LAST (never ranked), and stays in the denominator, so
cumulative % reaches 100 at the final bar. "Vital few" = the smallest set of top-ranked categories whose
cumulative share of ALL events (incl. Unclassified) reaches 80%.
Ranking robustness: Kendall tau-b of category values, count vs severity / class1 / single-rule-match-only.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import kendalltau  # noqa: E402

from ..metrics import record_metric  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CLASSIFIED = ROOT / "data" / "processed" / "events_classified.parquet"
TABLE = ROOT / "reports" / "tables" / "pareto.csv"
TAU_TABLE = ROOT / "reports" / "tables" / "pareto_rank_comparison.csv"
FIGDIR = ROOT / "reports" / "figures"
UNCL = "UNCLASSIFIED"
THRESHOLD = 0.80
SRC = "analysis/pareto.py"
PRIMARY, MUTED, INK, MUTED_INK = "#2a78d6", "#c9c7c1", "#1f1f1e", "#6b6963"


def pareto(values: pd.Series, threshold: float = THRESHOLD) -> pd.DataFrame:
    """values indexed by category -> sorted Pareto table with share, cum_share, rank, vital_few."""
    v = values.astype(float)
    ranked = v.drop(UNCL, errors="ignore").sort_values(ascending=False, kind="mergesort")
    order = list(ranked.index) + ([UNCL] if UNCL in v.index else [])
    total = v.sum()
    t = pd.DataFrame({"category": order, "value": v.reindex(order).to_numpy()})
    t["share"] = t["value"] / total if total else 0.0
    t["cum_share"] = t["share"].cumsum()
    t["rank"] = [i + 1 if c != UNCL else pd.NA for i, c in enumerate(t["category"])]
    # vital few: ranked categories up to and including the first one where cum_share >= threshold
    ranked_mask = t["category"] != UNCL
    reached = (t["cum_share"] >= threshold - 1e-12) & ranked_mask
    cutoff = reached.idxmax() if reached.any() else ranked_mask[ranked_mask].index.max()
    t["vital_few"] = ranked_mask & (t.index <= cutoff)
    if total:
        assert abs(t["cum_share"].iloc[-1] - 1.0) < 1e-9, "cumulative % must reach 100"
    return t


def view_values(df: pd.DataFrame, weight: str) -> pd.Series:
    if weight == "count":
        return df.groupby("category").size()
    if weight == "severity":
        return df.groupby("category")["class_severity"].sum()
    if weight == "class1":
        return df[df["classification"] == "Class I"].groupby("category").size()
    raise ValueError(weight)


def trailing_window(df: pd.DataFrame, months: int = 60) -> tuple[pd.DataFrame, str]:
    """Last `months` COMPLETE report months (the partial latest month is excluded)."""
    last = df["report_month"].max()  # partial month -> drop it
    end = last - pd.DateOffset(months=1)
    start = end - pd.DateOffset(months=months - 1)
    sub = df[(df["report_month"] >= start) & (df["report_month"] <= end)]
    return sub, f"{start:%Y-%m}..{end:%Y-%m}"


def tau(a: pd.Series, b: pd.Series) -> float:
    idx = sorted((set(a.index) | set(b.index)) - {UNCL})
    return float(kendalltau(a.reindex(idx, fill_value=0), b.reindex(idx, fill_value=0)).statistic)


def plot(t: pd.DataFrame, title: str, subtitle: str, path: Path) -> None:
    t = t.iloc[::-1]  # largest at top
    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    colors = [MUTED if c == UNCL else (PRIMARY if vf else MUTED) for c, vf in zip(t.category, t.vital_few)]
    bars = ax.barh(t["category"], t["value"], color=colors, height=0.72, edgecolor="white", linewidth=1)
    for b, c in zip(bars, t.category):
        if c == UNCL:
            b.set_hatch("///")
            b.set_edgecolor("#8a8781")
    xmax = t["value"].max()
    for y, (v, cs, vf) in enumerate(zip(t["value"], t["cum_share"], t["vital_few"])):
        ax.text(v + xmax * 0.01, y, f"{int(v):,}   cum {cs:.0%}", va="center", fontsize=8,
                color=INK if vf else MUTED_INK)
    ax.set_xlim(0, xmax * 1.28)
    ax.set_xlabel("Recall events (count)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED_INK, labelsize=9)
    ax.grid(axis="x", color="#ecebe8", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    import textwrap
    ax.set_title("\n".join(textwrap.wrap(subtitle, 110)), loc="left", fontsize=8.5, color=MUTED_INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    df = pd.read_parquet(CLASSIFIED)
    as_of = df["report_month"].max()
    rows, taus = [], []
    for pt in ("Drugs", "Food"):
        d_all = df[df["product_type"] == pt]
        win, win_label = trailing_window(d_all)
        for period, d, plabel in (("full", d_all, f"{d_all.report_month.min():%Y-%m}..{as_of:%Y-%m}"),
                                  ("trailing_60m", win, win_label)):
            vals = {w: view_values(d, w) for w in ("count", "severity", "class1")}
            for w, v in vals.items():
                t = pareto(v)
                t.insert(0, "weight", w)
                t.insert(0, "period", f"{period} ({plabel})")
                t.insert(0, "product_type", pt)
                rows.append(t)
                if w == "count":
                    vf = t[t.vital_few]
                    k, share = len(vf), vf["share"].sum()
                    unc = t.loc[t.category == UNCL, "share"].sum()
                    n_cat = int(((t.category != UNCL) & (t.value > 0)).sum())
                    plot(t, f"{pt}: {k} of {n_cat} root-cause categories account for {share:.0%} of recall events",
                         f"openFDA enforcement reports, {plabel}, n={len(d):,} events; keyword-rule categories; "
                         f"blue = vital few (to 80% cumulative); hatched = Unclassified ({unc:.0%}). "
                         "Counts, not rates.",
                         FIGDIR / f"pareto_{pt.lower()}_{period}.png")
                    if period == "full":
                        key = pt.lower()
                        record_metric(f"pareto.{key}.vital_few_k", k, SRC, note=f"count view, {plabel}")
                        record_metric(f"pareto.{key}.vital_few_share", round(share, 3), SRC,
                                      note=f"share of all events incl. Unclassified, {plabel}")
                        record_metric(f"pareto.{key}.vital_few", ", ".join(vf.category), SRC)
                        record_metric(f"pareto.{key}.unclassified_share", round(unc, 3), SRC)
            single = view_values(d[d["match_bucket"] == "single"], "count")
            for other, v in (("severity", vals["severity"]), ("class1", vals["class1"]),
                             ("single_match_only", single)):
                taus.append({"product_type": pt, "period": period, "comparison": f"count vs {other}",
                             "kendall_tau_b": round(tau(vals["count"], v), 3)})
    out = pd.concat(rows, ignore_index=True)
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLE, index=False)
    tt = pd.DataFrame(taus)
    tt.to_csv(TAU_TABLE, index=False)
    record_metric("pareto.min_kendall_tau", float(tt["kendall_tau_b"].min()), SRC,
                  note="minimum over product_type x period x comparison; see reports/tables/pareto_rank_comparison.csv")
    print(tt.to_string(index=False))
    print(out[(out.weight == "count") & out.vital_few][["product_type", "period", "category", "cum_share"]]
          .to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
