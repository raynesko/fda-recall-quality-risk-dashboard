"""Sensitivity of the latest risk ranking and flags (T5.1.3).

    python -m fda_recall.risk.sensitivity

Scored month = latest complete month. Three perturbation families, each compared with the default:
  (a) weights   - 1,000 Dirichlet(1,...,1) draws (seed 42)
  (b) window    - trailing window 6 / 24 months instead of 12 (min-volume guard scaled: 10 * window / 12)
  (c) labels    - 200 runs; a share of rule-accepted events equal to the measured error rate
                  (1 - clf.prod_precision_accepted_all) is reassigned uniformly to another category seen
                  in the same product type (seed 42)
Kendall tau-b (score ranking vs default, within product type) and per-category flag stability
(% of runs flagged) are reported. Fragile flag = default-flagged unit flagged in < 60% of runs of a family.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import kendalltau  # noqa: E402

from ..metrics import DEFAULT_PATH, record_metric  # noqa: E402
from .score import MIN_VOLUME, WEIGHTS, load_events, raw_components, score_frame  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
TABLE = ROOT / "reports" / "tables" / "flag_stability.csv"
TAU_TABLE = ROOT / "reports" / "tables" / "sensitivity_tau.csv"
FIG = ROOT / "reports" / "figures" / "risk_rank_stability.png"
REPORT = ROOT / "reports" / "sensitivity.md"
SRC = "risk/sensitivity.py"
SEED = 42
N_WEIGHTS, N_NOISE = 1000, 200
KEY = ["product_type", "category"]
PRIMARY, MUTED, INK, MUTED_INK = "#2a78d6", "#c9c7c1", "#1f1f1e", "#6b6963"


def taus(default: pd.DataFrame, other: pd.DataFrame) -> dict[str, float]:
    m = default.merge(other, on=KEY, suffixes=("", "_o"))
    return {pt: float(kendalltau(g["score"], g["score_o"]).statistic) for pt, g in m.groupby("product_type")}


def inject_noise(ev: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    e = ev.copy()
    acc = e.index[e["method"] == "rules"]
    pick = rng.choice(acc, size=int(round(rate * len(acc))), replace=False)
    cats = {pt: sorted(set(g.loc[g.method == "rules", "category"])) for pt, g in e.groupby("product_type")}
    new = []
    for i in pick:
        pool = [c for c in cats[e.at[i, "product_type"]] if c != e.at[i, "category"]]
        new.append(pool[rng.integers(len(pool))])
    e.loc[pick, "category"] = new
    return e


def main() -> int:
    ev = load_events()
    first, last = ev["report_month"].min(), ev["report_month"].max()
    start, t = first + pd.DateOffset(months=1), last - pd.DateOffset(months=1)
    rng = np.random.default_rng(SEED)

    raw = raw_components(ev, t, start)
    base = score_frame(raw)
    default = base[KEY + ["score", "flag"]]
    runs: list[pd.DataFrame] = []
    tau_rows = []

    # (a) weights
    names = list(WEIGHTS)
    ranks = []
    for i in range(N_WEIGHTS):
        w = dict(zip(names, rng.dirichlet(np.ones(len(names)))))
        s = score_frame(raw, weights=w)
        runs.append(s[KEY + ["flag"]].assign(family="weights", run=i))
        tau_rows += [{"family": "weights", "run": i, "product_type": pt, "tau": v} for pt, v in taus(default, s).items()]
        ranks.append(s.assign(rank=s.groupby("product_type")["score"].rank(ascending=False, method="min"))[KEY + ["rank"]])

    # (b) window
    for win in (6, 24):
        s = score_frame(raw_components(ev, t, start, window=win), min_volume=int(round(MIN_VOLUME * win / 12)))
        runs.append(s[KEY + ["flag"]].assign(family="window", run=win))
        tau_rows += [{"family": f"window_{win}m", "run": win, "product_type": pt, "tau": v} for pt, v in taus(default, s).items()]

    # (c) label noise
    m = json.loads(Path(DEFAULT_PATH).read_text(encoding="utf-8"))
    rate = round(1 - m["clf.prod_precision_accepted_all"]["value"], 3)
    for i in range(N_NOISE):
        s = score_frame(raw_components(inject_noise(ev, rate, rng), t, start))
        runs.append(s[KEY + ["flag"]].assign(family="label_noise", run=i))
        tau_rows += [{"family": "label_noise", "run": i, "product_type": pt, "tau": v} for pt, v in taus(default, s).items()]

    r = pd.concat(runs, ignore_index=True)
    stab = r.pivot_table(index=KEY, columns="family", values="flag", aggfunc="mean").mul(100).round(1)
    stab.columns = [f"flag_pct_{c}" for c in stab.columns]
    stab = default.set_index(KEY)[["flag", "score"]].rename(columns={"flag": "default_flag", "score": "default_score"}) \
        .join(stab).reset_index().sort_values(["product_type", "default_score"], ascending=[True, False])
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    stab.to_csv(TABLE, index=False)
    tt = pd.DataFrame(tau_rows)
    tsum = tt.groupby(["family", "product_type"])["tau"].median().round(3).reset_index()
    tsum.to_csv(TAU_TABLE, index=False)

    fam_cols = [c for c in stab.columns if c.startswith("flag_pct_")]
    fragile = stab[stab.default_flag & (stab[fam_cols].min(axis=1) < 60)]
    med_w = float(tt[tt.family == "weights"]["tau"].median())
    record_metric("sens.median_tau_weights", round(med_w, 3), SRC,
                  note=f"1,000 Dirichlet draws, both product types pooled, month {t:%Y-%m}; TARGET >= 0.70")
    record_metric("sens.median_tau_label_noise", round(float(tt[tt.family == "label_noise"]["tau"].median()), 3), SRC,
                  note=f"{N_NOISE} runs at noise rate {rate}")
    for win in (6, 24):
        record_metric(f"sens.tau_window_{win}m", round(float(tt[tt.family == f"window_{win}m"]["tau"].mean()), 3), SRC,
                      note="mean over product types")
    record_metric("sens.n_default_flags", int(stab.default_flag.sum()), SRC)
    record_metric("sens.fragile_flags", "; ".join(f"{a}/{b}" for a, b in zip(fragile.product_type, fragile.category)) or "none",
                  SRC, note="default-flagged units flagged in <60% of runs in at least one family")

    # rank-stability chart: distribution of rank under weight draws, per product type
    rk = pd.concat(ranks, ignore_index=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharex=False)
    for ax, (pt, g) in zip(axes, rk.groupby("product_type")):
        order = base[base.product_type == pt].sort_values("score", ascending=False)["category"].tolist()
        data = [g[g.category == c]["rank"].to_numpy() for c in order]
        ax.boxplot(data, orientation="horizontal", tick_labels=order, widths=0.55, patch_artist=True, showfliers=False,
                   boxprops={"facecolor": "#dbe8f8", "edgecolor": PRIMARY}, medianprops={"color": PRIMARY, "linewidth": 2},
                   whiskerprops={"color": MUTED_INK}, capprops={"color": MUTED_INK})
        d = base[base.product_type == pt].set_index("category")
        drank = d["score"].rank(ascending=False, method="min")
        ax.scatter([drank[c] for c in order], range(1, len(order) + 1), marker="D", s=26, color=INK, zorder=5,
                   label="Default-weight rank")
        for y, c in enumerate(order, start=1):
            if d.loc[c, "flag"]:
                ax.text(len(order) + 0.6, y, "flagged", va="center", fontsize=7.5, color=INK)
        ax.invert_yaxis()
        ax.set_xlim(0.5, len(order) + 2.6)
        ax.set_title(pt, loc="left", fontsize=10, color=INK)
        ax.set_xlabel("Rank within product type (1 = highest score)")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(colors=MUTED_INK, labelsize=8)
        ax.grid(axis="x", color="#ecebe8", linewidth=0.8)
        ax.set_axisbelow(True)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper right", bbox_to_anchor=(0.99, 0.93), fontsize=8, frameon=False)
    fig.suptitle(f"Risk ranks under 1,000 random weightings: median Kendall tau vs default = {med_w:.2f}",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.text(0.01, 0.905, f"Boxes = interquartile range of rank, whiskers 1.5 IQR; month scored {t:%Y-%m}; "
             "openFDA recall events, keyword-rule categories.", fontsize=8, color=MUTED_INK)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(FIG, dpi=150)
    plt.close(fig)

    L = ["# Risk-Score Sensitivity (T5.1.3)", "",
         f"Month scored: {t:%Y-%m}. Values in `results/metrics.json` under `sens.*`; tables "
         "`reports/tables/flag_stability.csv`, `reports/tables/sensitivity_tau.csv`; figure `reports/figures/risk_rank_stability.png`.", "",
         "## Median Kendall tau vs default ranking", "", tsum.to_markdown(index=False), "",
         f"Target (weights, median tau >= 0.70): **{'met' if med_w >= 0.70 else 'MISSED'}** ({med_w:.3f}).", "",
         "## Flag stability (% of runs flagged)", "", stab.round(3).to_markdown(index=False), "",
         "## Fragile flags (< 60% in at least one family)", "",
         ("\n".join(f"- {a} / {b}" for a, b in zip(fragile.product_type, fragile.category)) or "- none"), "",
         f"Label noise rate {rate} = 1 - precision on accepted predictions (gold set). Noise is uniform over other "
         "categories, which is harsher than real confusions (those concentrate in overlapping pairs)."]
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
