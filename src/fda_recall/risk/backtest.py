"""Rolling-origin backtest of the risk score vs naive baselines (T5.1.2).

    python -m fda_recall.risk.backtest

Implements exactly the pre-registered plan in docs/methodology/risk-score.md (hash checked at start).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ..metrics import DEFAULT_PATH, record_metric
from .score import PSEUDO, load_events, months_back, raw_components, score_at

ROOT = Path(__file__).resolve().parents[3]
PREREG = ROOT / "docs" / "methodology" / "risk-score.md"
REPORT = ROOT / "reports" / "backtest.md"
CELLS = ROOT / "reports" / "tables" / "backtest_cells.csv"
UNITS = ROOT / "reports" / "tables" / "backtest_units.csv"
SRC = "risk/backtest.py"
SEED = 42
K = 3
MIN_ELIGIBLE = 6
MIN_T12 = 10


def outcome(ev: pd.DataFrame, t: pd.Timestamp) -> pd.DataFrame:
    """Events and Class I share in t+1..t+12 per unit (uses the future - only for evaluation)."""
    fut = ev[(ev["report_month"] > t) & (ev["report_month"] <= months_back(t, -12))]
    g = fut.groupby(["product_type", "category"]).agg(
        n_next=("event_id", "size"), c1_next=("classification", lambda s: (s == "Class I").sum()))
    return g.reset_index()


def topk_hits(sel: pd.Series, delta: pd.Series, k: int = K) -> float:
    """Share of the k units with highest `sel` whose delta ranks in the top k (ties in delta -> min rank)."""
    chosen = sel.sort_values(ascending=False, kind="mergesort").index[:k]
    hit = delta.rank(method="min", ascending=False) <= k
    return float(hit.loc[chosen].mean())


def build_units(ev: pd.DataFrame, origins, start: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for t in origins:
        s = score_at(ev, t, start)
        o = outcome(ev, t)
        u = s.merge(o, on=["product_type", "category"], how="left").fillna({"n_next": 0, "c1_next": 0})
        u["delta"] = np.log((u["n_next"] + PSEUDO) / (u["t12"] + PSEUDO))
        win = ev[(ev["report_month"] > months_back(t, 12)) & (ev["report_month"] <= t)]
        c1_now = win.groupby(["product_type", "category"])["classification"].apply(lambda s: (s == "Class I").mean())
        u = u.merge(c1_now.rename("c1_share_now").reset_index(), on=["product_type", "category"], how="left")
        u["c1_share_next"] = np.where(u["n_next"] > 0, u["c1_next"] / u["n_next"].where(u["n_next"] > 0, 1), np.nan)
        u["c1_share_change"] = u["c1_share_next"] - u["c1_share_now"]
        u["origin"] = t
        rows.append(u)
    return pd.concat(rows, ignore_index=True)


def cell_table(units: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    el = units[units["t12"] >= MIN_T12]
    out, dropped = [], 0
    for (t, pt), c in el.groupby(["origin", "product_type"]):
        if len(c) < MIN_ELIGIBLE:
            dropped += 1
            continue
        c = c.set_index("category")
        n_hits = int((c["delta"].rank(method="min", ascending=False) <= K).sum())
        out.append({"origin": t, "product_type": pt, "n_eligible": len(c),
                    "score": topk_hits(c["score"], c["delta"]), "B1_volume": topk_hits(c["t12"], c["delta"]),
                    "B2_momentum": topk_hits(c["momentum"], c["delta"]),
                    "B3_random_expected": n_hits / len(c)})  # E[p@3] of a random 3 of m units with h hits
    return pd.DataFrame(out), dropped


def permutation_p(units: pd.DataFrame, obs: float, n: int = 1000, seed: int = SEED) -> float:
    rng = np.random.default_rng(seed)
    el = units[units["t12"] >= MIN_T12]
    cells = [c.set_index("category") for _, c in el.groupby(["origin", "product_type"]) if len(c) >= MIN_ELIGIBLE]
    ge = 0
    for _ in range(n):
        vals = [topk_hits(pd.Series(rng.permutation(c["score"].to_numpy()), index=c.index), c["delta"])
                for c in cells]
        ge += np.mean(vals) >= obs - 1e-12
    return (1 + ge) / (n + 1)


def sign_flip_p(d: np.ndarray, n: int = 10000, seed: int = SEED) -> float:
    rng = np.random.default_rng(seed)
    obs = d.mean()
    flips = rng.choice([-1, 1], size=(n, len(d)))
    return float((1 + ((flips * d).mean(1) >= obs - 1e-12).sum()) / (n + 1))


def block_boot(df: pd.DataFrame, stat, n: int = 2000, seed: int = SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    origins = df["origin"].unique()
    groups = {o: df[df["origin"] == o] for o in origins}
    vals = []
    for _ in range(n):
        pick = rng.choice(origins, len(origins), replace=True)
        v = stat(pd.concat([groups[o] for o in pick], ignore_index=True))
        if np.isfinite(v):
            vals.append(v)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def rho(df: pd.DataFrame, col: str = "score") -> float:
    return float(spearmanr(df[col], df["delta"]).statistic) if len(df) > 2 else np.nan


def main() -> int:
    recorded = json.loads(Path(DEFAULT_PATH).read_text(encoding="utf-8"))["risk.preregistration_sha256"]["value"]
    current = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    prereg_ok = recorded == current
    record_metric("backtest.preregistration_hash_match", prereg_ok, SRC)

    ev = load_events()
    first, last = ev["report_month"].min(), ev["report_month"].max()
    start, end = first + pd.DateOffset(months=1), last - pd.DateOffset(months=1)
    last_origin = months_back(end, 12)
    desc_origins = list(pd.date_range("2016-06-01", last_origin, freq="6MS"))
    inf_origins = [o for o in desc_origins if o.month == 6]

    # leakage check on real data at one origin
    t0 = inf_origins[len(inf_origins) // 2]
    a = raw_components(ev, t0, start)
    b = raw_components(ev[ev["report_month"] <= t0], t0, start)
    pd.testing.assert_frame_equal(a, b)
    record_metric("backtest.leakage_check_passed", True, SRC, note=f"real data, origin {t0:%Y-%m}")

    units = build_units(ev, desc_origins, start)
    UNITS.parent.mkdir(parents=True, exist_ok=True)
    units.to_csv(UNITS, index=False)
    inf_units = units[units["origin"].isin(inf_origins)]
    el = inf_units[inf_units["t12"] >= MIN_T12]

    cells, dropped = cell_table(inf_units)
    desc_cells, _ = cell_table(units)
    cells.to_csv(CELLS, index=False)
    n_orig, n_cells, n_units = len(inf_origins), len(cells), len(el)
    tag = f"{n_orig} yearly origins {inf_origins[0]:%Y-%m}..{inf_origins[-1]:%Y-%m}, {n_cells} origin x product cells, {n_units} eligible unit-origins"

    p = {m: float(cells[m].mean()) for m in ("score", "B1_volume", "B2_momentum", "B3_random_expected")}
    best_base = max(("B1_volume", "B2_momentum", "B3_random_expected"), key=lambda m: p[m])
    r = rho(el)
    r_ci = block_boot(el, rho)
    r_mom = rho(el, "momentum")
    r_mom_ci = block_boot(el, lambda d: rho(d, "momentum"))
    perm_p = permutation_p(inf_units, p["score"])
    res = {}
    for m in ("B1_volume", "B2_momentum"):
        d = (cells["score"] - cells[m]).to_numpy()
        res[m] = (float(d.mean()), sign_flip_p(d),
                  block_boot(cells.assign(d=d), lambda x: x["d"].mean()))
    met_p = p["score"] >= p[best_base] + 0.15
    met_r = r_ci[0] > 0
    flagged = el[el["flag"]]
    sec = (float(flagged["c1_share_change"].mean()), float(el[~el["flag"]]["c1_share_change"].mean()))

    for m, v in p.items():
        record_metric(f"backtest.p_at_3.{m}", round(v, 3), SRC, note=tag)
    record_metric("backtest.p_at_3", round(p["score"], 3), SRC, note=tag)
    record_metric("backtest.best_baseline", best_base, SRC)
    record_metric("backtest.best_baseline_p_at_3", round(p[best_base], 3), SRC, note=tag)
    record_metric("backtest.score_perm_p", round(perm_p, 4), SRC, note="one-sided, 1,000 within-cell shuffles")
    for m, (dm, pv, ci) in res.items():
        record_metric(f"backtest.diff_vs_{m}", round(dm, 3), SRC,
                      note=f"sign-flip p={pv:.4f}; block-bootstrap 95% CI {ci[0]:.3f}..{ci[1]:.3f}; {tag}")
    record_metric("backtest.spearman_rho", round(r, 3), SRC, note=tag)
    record_metric("backtest.spearman_rho_ci", [round(r_ci[0], 3), round(r_ci[1], 3)], SRC,
                  note="block bootstrap over origins, 2,000")
    record_metric("backtest.momentum_rho", round(r_mom, 3), SRC,
                  note=f"regression-to-the-mean check; CI {r_mom_ci[0]:.3f}..{r_mom_ci[1]:.3f}")
    record_metric("backtest.target_met", bool(met_p and met_r), SRC,
                  note=f"p@3 criterion {'met' if met_p else 'missed'}; rho criterion {'met' if met_r else 'missed'}")
    record_metric("backtest.n_origins", n_orig, SRC)
    record_metric("backtest.n_cells", n_cells, SRC, note=f"{dropped} cells dropped (<{MIN_ELIGIBLE} eligible units)")

    dp = {m: float(desc_cells[m].mean()) for m in p}
    L = ["# Risk-Score Backtest (T5.1.2)", "",
         f"Pre-registered plan: `docs/methodology/risk-score.md` (hash match: **{prereg_ok}**). "
         "All numbers are in `results/metrics.json` under `backtest.*`.", "",
         f"**Design:** {tag}. Origins every 12 months (non-overlapping 12-month outcome windows) for inference; "
         f"{len(desc_origins)} six-monthly origins descriptive only. Eligible unit = product_type x category with "
         f">= {MIN_T12} events in the 12 months before the origin; {dropped} cells dropped for < {MIN_ELIGIBLE} eligible units. "
         "Outcome = log change in events, next 12 months vs trailing 12 months. Leakage check on real data passed.", "",
         "## Precision@3 (hit = unit's outcome ranks in the cell's top 3)", "",
         "| method | inference (yearly) | descriptive (6-monthly) |", "|---|---|---|"]
    for m in p:
        L.append(f"| {m} | {p[m]:.3f} | {dp[m]:.3f} |")
    L += ["", f"Score permutation test (within-cell shuffles, one-sided): p = {perm_p:.4f}.", ""]
    for m, (dm, pv, ci) in res.items():
        L.append(f"- Score minus {m}: {dm:+.3f} per cell, sign-flip p = {pv:.4f}, block-bootstrap 95% CI {ci[0]:+.3f} to {ci[1]:+.3f} (n = {n_cells} cells).")
    L += ["", "## Rank correlation", "",
          f"- Spearman rho(score, outcome) = {r:.3f}, 95% CI {r_ci[0]:.3f} to {r_ci[1]:.3f} (n = {n_units} eligible unit-origins, {n_orig} origins).",
          f"- Regression to the mean: rho(momentum, outcome) = {r_mom:.3f}, 95% CI {r_mom_ci[0]:.3f} to {r_mom_ci[1]:.3f}. "
          "A negative value means categories that just rose tended to fall back.", "",
          "## Secondary (descriptive)", "",
          f"Mean change in Class I share, next 12 m vs trailing 12 m: flagged units {sec[0]:+.3f}, not flagged {sec[1]:+.3f}.", "",
          "## Verdict against pre-registered targets", "",
          f"- precision@3(score) >= best baseline ({best_base}, {p[best_base]:.3f}) + 0.15: **{'met' if met_p else 'MISSED'}** ({p['score']:.3f}).",
          f"- rho 95% CI excludes 0 on the positive side: **{'met' if met_r else 'MISSED'}**.", "",
          ("**Target met.**" if met_p and met_r else
           "**Target missed.** Per the pre-registration, weights are not re-tuned and the score is presented as a "
           "transparent monitoring/triage framework evaluated against 3 naive baselines, with no predictive claim."), "",
          "Caveats: few origins and units, so every interval is wide; categories come from keyword rules with "
          "precision ~0.90 on accepted predictions (label-noise sensitivity in T5.1.3); counts reflect FDA "
          "enforcement and reporting as well as industry failures."]
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
