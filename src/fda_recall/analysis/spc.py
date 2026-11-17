"""Control charts: c-chart and p-chart with Laney adjustment and run rules (T4.2.2).

    python -m fda_recall.analysis.spc

Method and caveats: docs/methodology/time-series.md. Limits describe the stability of FDA-recorded recall
activity per category - not firm quality, not failure rates.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ..metrics import record_metric  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SERIES = ROOT / "data" / "processed" / "series_monthly.parquet"
OUT = ROOT / "data" / "processed" / "spc_signals.parquet"
TABLES = ROOT / "reports" / "tables"
FIGDIR = ROOT / "reports" / "figures"
SRC = "analysis/spc.py"
D2 = 1.128
RUN = 8
SEED = 42
DEFAULT_BASELINE = ("2015-01-01", "2019-12-01")
ALT_BASELINES = [("2013-01-01", "2017-12-01"), ("2016-01-01", "2020-12-01"), ("2018-01-01", "2022-12-01")]
MIN_BASELINE_MEAN = 1.0
UNCL = "UNCLASSIFIED"
PRIMARY, MUTED, INK, MUTED_INK, SIGNAL = "#2a78d6", "#c9c7c1", "#1f1f1e", "#6b6963", "#d1495b"


# ---------- pure chart math -------------------------------------------------------------------------
def laney_sigma_z(z: np.ndarray) -> float:
    """Laney sigma_z = mean moving range of z / d2. Needs >= 2 points."""
    z = np.asarray(z, float)
    if len(z) < 2:
        return 1.0
    return float(np.mean(np.abs(np.diff(z))) / D2)


def c_params(baseline: np.ndarray) -> tuple[float, float, float]:
    """-> (cl, sigma, sigma_z) for a c-chart. sigma is the Poisson sigma sqrt(cl)."""
    b = np.asarray(baseline, float)
    cl = float(b.mean())
    sigma = float(np.sqrt(cl))
    sz = laney_sigma_z((b - cl) / sigma) if sigma > 0 else 1.0
    return cl, sigma, sz


def p_params(x: np.ndarray, n: np.ndarray) -> tuple[float, float]:
    """-> (pbar, sigma_z) for a p-chart from baseline counts x out of n."""
    x, n = np.asarray(x, float), np.asarray(n, float)
    keep = n > 0
    pbar = float(x[keep].sum() / n[keep].sum())
    s = np.sqrt(pbar * (1 - pbar) / n[keep])
    sz = laney_sigma_z(((x[keep] / n[keep]) - pbar) / s) if pbar * (1 - pbar) > 0 else 1.0
    return pbar, sz


def limits(cl: float, sigma: np.ndarray | float, sigma_z: float) -> tuple[np.ndarray, np.ndarray]:
    """3-sigma limits, widened by Laney sigma_z only when sigma_z > 1; LCL floored at 0."""
    k = 3 * np.asarray(sigma, float) * max(sigma_z, 1.0)
    return cl + k, np.maximum(cl - k, 0.0)


def rule1(v: np.ndarray, ucl: np.ndarray, lcl: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    return (v > ucl) | ((v < lcl) & (lcl > 0))


def rule2(v: np.ndarray, cl: float, run: int = RUN) -> np.ndarray:
    """Flag the run-th and later points of a run of >= run consecutive points on one side of cl."""
    side = np.sign(np.asarray(v, float) - cl)
    out = np.zeros(len(side), bool)
    count, prev = 0, 0
    for i, s in enumerate(side):
        count = count + 1 if (s != 0 and s == prev) else (1 if s != 0 else 0)
        prev = s
        out[i] = count >= run
    return out


def chart(values: np.ndarray, in_base: np.ndarray, kind: str, n: np.ndarray | None = None,
          max_iter: int = 10) -> dict:
    """Fit Phase I (iteratively dropping rule-1 points), then score every point.

    Returns dict with arrays cl, ucl, lcl, r1, r2, and the list of removed baseline indices."""
    v = np.asarray(values, float)
    keep = np.asarray(in_base, bool).copy()
    removed: list[int] = []
    for _ in range(max_iter):
        if kind == "c":
            cl, sigma, sz = c_params(v[keep])
            sig = np.full(len(v), sigma)
        else:
            cl, sz = p_params((v * n)[keep], n[keep])
            with np.errstate(divide="ignore", invalid="ignore"):
                sig = np.where(n > 0, np.sqrt(cl * (1 - cl) / n), np.nan)
        ucl, lcl = limits(cl, sig, sz)
        out = keep & rule1(v, ucl, lcl)
        if not out.any():
            break
        removed += list(np.flatnonzero(out))
        keep &= ~out
    return {"cl": np.full(len(v), cl), "ucl": ucl, "lcl": lcl, "sigma_z": sz,
            "r1": rule1(v, ucl, lcl), "r2": rule2(v, cl), "removed": removed}


def rule_id(r1: bool, r2: bool) -> str:
    return "+".join(r for r, f in (("R1", r1), ("R2", r2)) if f)


# ---------- simulation ------------------------------------------------------------------------------
def simulate_false_alarms(lam: float, n_series: int = 1000, n: int = 60, seed: int = SEED) -> dict:
    """Stable Poisson series; limits estimated from the same 60 points (Phase I = whole series)."""
    rng = np.random.default_rng(seed)
    r1_pts = r2_pts = r1_any = r2_any = 0
    for _ in range(n_series):
        x = rng.poisson(lam, n).astype(float)
        if x.sum() == 0:
            continue
        res = chart(x, np.ones(n, bool), "c", max_iter=1)
        r1_pts += res["r1"].sum()
        r2_pts += res["r2"].sum()
        r1_any += res["r1"].any()
        r2_any += res["r2"].any()
    tot = n_series * n
    return {"lambda": lam, "r1_per_point": r1_pts / tot, "r2_per_point": r2_pts / tot,
            "r1_any_in_series": r1_any / n_series, "r2_any_in_series": r2_any / n_series}


# ---------- pipeline --------------------------------------------------------------------------------
def run_all(g: pd.DataFrame, baseline: tuple[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    b0, b1 = map(pd.Timestamp, baseline)
    rows, removed = [], []
    for (pt, cat), s in g.groupby(["product_type", "category"], sort=True):
        s = s.sort_values("month").reset_index(drop=True)
        in_base = s["month"].between(b0, b1).to_numpy()
        base_mean = s.loc[in_base, "n_events"].mean()
        monitored = bool(base_mean >= MIN_BASELINE_MEAN and cat != UNCL)
        for kind, vals, n in (("c", s["n_events"].to_numpy(float), None),
                              ("p", s["share"].to_numpy(float), s["month_total"].to_numpy(float))):
            res = chart(vals, in_base, kind, n)
            out = s[["product_type", "category", "month", "n_events", "month_total"]].copy()
            out["chart"], out["value"] = kind, vals
            out["phase"] = np.where(in_base, "I", np.where(s["month"] > b1, "II", "pre"))
            out["cl"], out["ucl"], out["lcl"] = res["cl"], res["ucl"], res["lcl"]
            out["sigma_z"] = res["sigma_z"]
            out["laney_applied"] = res["sigma_z"] > 1
            out["r1"], out["r2"] = res["r1"], res["r2"]
            out["signal"] = out["r1"] | out["r2"]
            out["rule_id"] = [rule_id(a, b) for a, b in zip(out.r1, out.r2)]
            out["phase1_removed"] = False
            out.loc[res["removed"], "phase1_removed"] = True
            out["monitored"] = monitored
            rows.append(out)
            removed += [{"product_type": pt, "category": cat, "chart": kind, "month": s.loc[i, "month"],
                         "value": vals[i]} for i in res["removed"]]
    return pd.concat(rows, ignore_index=True), pd.DataFrame(removed)


def summarize(sig: pd.DataFrame) -> pd.DataFrame:
    m = sig[sig.monitored & (sig.phase == "II")]
    return (m.groupby("chart").agg(series=("category", lambda s: s.groupby(m.loc[s.index, "product_type"]).nunique().sum()),
                                   r1=("r1", "sum"), r2=("r2", "sum"), any_signal=("signal", "sum"))
            .reset_index())


def plot_p(sig: pd.DataFrame, pt: str, cat: str, path: Path, as_of: str) -> None:
    s = sig[(sig.product_type == pt) & (sig.category == cat) & (sig.chart == "p")].sort_values("month")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(s.month, s.value * 100, color=PRIMARY, linewidth=1.6, label="Monthly share")
    ax.plot(s.month, s.ucl * 100, color=MUTED_INK, linewidth=1, linestyle="--", label="UCL / LCL")
    ax.plot(s.month, s.lcl * 100, color=MUTED_INK, linewidth=1, linestyle="--")
    ax.plot(s.month, s.cl * 100, color=MUTED_INK, linewidth=1, label="Centre line (Phase I)")
    b = s[s.phase == "I"]
    ax.axvspan(b.month.min(), b.month.max(), color="#f0efec", zorder=0, label="Phase I baseline")
    r1, r2 = s[s.r1], s[s.r2 & ~s.r1]
    ax.scatter(r1.month, r1.value * 100, marker="^", s=46, color=SIGNAL, zorder=5, edgecolor="white",
               linewidth=1, label="R1: beyond limit")
    ax.scatter(r2.month, r2.value * 100, marker="o", s=30, facecolor="white", edgecolor=SIGNAL, zorder=5,
               linewidth=1.4, label="R2: 8-point run")
    n2 = int((s[s.phase == "II"].signal).sum())
    lan = " (Laney-adjusted)" if s.laney_applied.iloc[0] else ""
    fig.suptitle(f"{pt} - {cat}: {n2} signalled months after the baseline", x=0.01, ha="left",
                 fontsize=12, fontweight="bold", color=INK)
    ax.set_title(f"p-chart of category share of monthly recall events{lan}; openFDA, report month, data as of {as_of}.\n"
                 "Describes FDA-recorded recall activity, not firm quality.", loc="left", fontsize=8, color=MUTED_INK)
    ax.set_ylabel("Share of the month's events (%)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(MUTED)
    ax.tick_params(colors=MUTED_INK, labelsize=8.5)
    ax.grid(axis="y", color="#ecebe8", linewidth=0.8)
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=7.5, ncol=6, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    g = pd.read_parquet(SERIES)
    sig, removed = run_all(g, DEFAULT_BASELINE)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sig.to_parquet(OUT, index=False)
    TABLES.mkdir(parents=True, exist_ok=True)
    removed.to_csv(TABLES / "spc_phase1_removed.csv", index=False)

    summ = summarize(sig)
    mon = sig[sig.monitored & (sig.chart == "p")].groupby(["product_type", "category"]).size()
    record_metric("spc.n_categories", int(len(mon)), SRC,
                  note=f"monitored product_type x category series (Phase I mean >= {MIN_BASELINE_MEAN}/month, excl. Unclassified)")
    record_metric("spc.baseline_window", f"{DEFAULT_BASELINE[0][:7]}..{DEFAULT_BASELINE[1][:7]}", SRC)
    for _, r in summ.iterrows():
        record_metric(f"spc.{r.chart}.phase2_signal_months", int(r.any_signal), SRC,
                      note=f"R1 {int(r.r1)}, R2 {int(r.r2)} (month can carry both)")
    p2 = sig[sig.monitored & (sig.phase == "II") & (sig.chart == "p")]
    with_sig = p2.groupby(["product_type", "category"])["signal"].any()
    record_metric("spc.n_signals", int(p2.signal.sum()), SRC, note="p-chart Phase II signalled category-months")
    record_metric("spc.n_categories_with_signal", int(with_sig.sum()), SRC, note="p-chart, Phase II")
    record_metric("spc.laney_share", round(float(sig[sig.monitored].groupby(["product_type", "category", "chart"])
                                                   .laney_applied.first().mean()), 3), SRC,
                  note="share of monitored charts where sigma_z > 1")

    # sensitivity to baseline window
    sens = [summarize(sig).assign(baseline=f"{DEFAULT_BASELINE[0][:7]}..{DEFAULT_BASELINE[1][:7]} (default)")]
    for w in ALT_BASELINES:
        s2, _ = run_all(g, w)
        sens.append(summarize(s2).assign(baseline=f"{w[0][:7]}..{w[1][:7]}"))
    sens_t = pd.concat(sens, ignore_index=True)[["baseline", "chart", "series", "r1", "r2", "any_signal"]]
    sens_t.to_csv(TABLES / "spc_window_sensitivity.csv", index=False)

    # false-alarm simulation
    sim = pd.DataFrame([simulate_false_alarms(lam) for lam in (1, 3, 10, 30)])
    sim.to_csv(TABLES / "spc_false_alarm_simulation.csv", index=False)
    for _, r in sim.iterrows():
        lam = int(r["lambda"])
        record_metric(f"spc.sim_lambda{lam}.r1_per_point", round(r.r1_per_point, 4), SRC,
                      note="1,000 stable Poisson series, n=60, seed 42; normal theory 0.0027")
        record_metric(f"spc.sim_lambda{lam}.r2_per_point", round(r.r2_per_point, 4), SRC)
        record_metric(f"spc.sim_lambda{lam}.any_signal_series", round(max(r.r1_any_in_series, r.r2_any_in_series), 3), SRC,
                      note="max of (share of series with >=1 R1, with >=1 R2)")

    # top 6 charts: top 3 drug + top 3 food categories by events in window
    as_of = f"{g.month.max():%Y-%m}"
    top = (g[g.category != UNCL].groupby(["product_type", "category"]).n_events.sum()
           .groupby(level=0, group_keys=False).nlargest(3))
    for (pt, cat) in top.index:
        plot_p(sig, pt, cat, FIGDIR / f"spc_{pt.lower()}_{cat.lower()}.png", as_of)

    print(summ.to_string(index=False))
    print(sens_t.to_string(index=False))
    print(sim.to_string(index=False))
    print("monitored", len(mon), "with signal", int(with_sig.sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
