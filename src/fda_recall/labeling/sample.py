"""Draw the 300-event gold-set sample (T3.1.2).

    python -m fda_recall.labeling.sample --seed 42

Design (recorded in docs/domain/labeling-guide.md):
  * 200 RANDOM events, stratified by product_type x report-year bucket, proportional allocation
    (largest-remainder rounding).
  * 100 TARGETED events drawn with broad search patterns so rare categories get >= ~10 examples.
    Targeted rows are flagged source=targeted; the sample is NOT prevalence-representative.
    Classifier metrics are reported on all 300 AND on the random-200 subset (targeted draws were found
    with keywords, which could favour the keyword baseline).
Writes data/labels/gold_v1.csv with an empty `label` column; existing labels are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EVENTS = ROOT / "data" / "processed" / "recalls_event.parquet"
OUT = ROOT / "data" / "labels" / "gold_v1.csv"
YEAR_BUCKETS = [(2012, 2015), (2016, 2019), (2020, 2022), (2023, 2026)]
# Sampling-only search patterns (broad on purpose; NOT the keyword baseline rules).
TARGET_PATTERNS = {
    "STERILITY": r"steril",
    "IMPURITY": r"impurit|nitros|ndma|benzene|lead|arsenic|aflatoxin|chemical",
    "UNAPPROVED": r"sildenafil|tadalafil|unapproved|without an approved",
    "FOREIGN": r"foreign|metal|glass|plastic|particulate",
    "MIXUP": r"mix-?up|wrong|commingl|foreign tablets|another product",
    "POTENCY": r"potent|assay|uniformity",
    "SPEC_FAIL": r"dissolution|stability|ph |viscosity|specification",
    "PACKAGING": r"container|seal|leak|closure|delivery system|crack",
    "PROCESS_SANITATION": r"insanitary|process|temperature|botulinum|refrigerat",
    "LABELING": r"label|misbrand|expir|package insert",
    "CGMP": r"cgmp|good manufacturing",
    "MICRO": r"listeria|salmonella|coli|mold|microbial",
    "ALLERGEN": r"undeclared (?:milk|egg|wheat|soy|peanut|tree nut|fish|shellfish|sesame|sulfite)",
}
COLUMNS = ["event_id", "product_type", "report_year", "source", "reason_text",
           "label", "secondary_label", "labeled_at", "notes"]


def _bucket(year: int) -> str:
    for lo, hi in YEAR_BUCKETS:
        if lo <= year <= hi:
            return f"{lo}-{hi}"
    raise ValueError(year)


def _alloc(sizes: pd.Series, n: int) -> pd.Series:
    raw = sizes / sizes.sum() * n
    base = np.floor(raw).astype(int)
    rem = n - base.sum()
    order = (raw - base).sort_values(ascending=False, kind="mergesort").index[:rem]
    base[order] += 1
    return base


def draw(ev: pd.DataFrame, seed: int = 42, n_random: int = 200, n_targeted: int = 100) -> pd.DataFrame:
    ev = ev.sort_values("event_id").reset_index(drop=True)
    ev["report_year"] = ev["report_date"].dt.year
    ev["stratum"] = ev["product_type"] + "|" + ev["report_year"].map(_bucket)
    rng = np.random.default_rng(seed)
    alloc = _alloc(ev.groupby("stratum").size(), n_random)
    picks = []
    for stratum, k in alloc.items():
        idx = ev.index[ev.stratum == stratum].to_numpy()
        picks += list(rng.choice(idx, size=k, replace=False))
    random_df = ev.loc[sorted(picks)].assign(source="random")

    remaining = ev.drop(index=picks)
    per = int(np.ceil(n_targeted / len(TARGET_PATTERNS)))
    targeted = []
    for _, pat in TARGET_PATTERNS.items():
        pool = remaining.index[remaining.reason_norm.str.contains(pat, regex=True)
                               & ~remaining.index.isin(targeted)].to_numpy()
        k = min(per, len(pool))
        targeted += list(rng.choice(pool, size=k, replace=False))
    targeted = targeted[:n_targeted]
    targeted_df = ev.loc[targeted].assign(source="targeted")

    out = pd.concat([random_df, targeted_df])
    out = out.sample(frac=1, random_state=seed)  # shuffle so labeler cannot tell source from order
    res = pd.DataFrame({"event_id": out.event_id, "product_type": out.product_type,
                        "report_year": out.report_year, "source": out.source,
                        "reason_text": out.reason_for_recall})
    for c in COLUMNS[5:]:
        res[c] = ""
    assert res.event_id.is_unique and len(res) == n_random + n_targeted
    return res[COLUMNS].reset_index(drop=True)


def id_hash(ids: pd.Series) -> str:
    return hashlib.sha256(",".join(ids.astype(str)).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--force", action="store_true", help="overwrite even if labels exist (dangerous)")
    a = ap.parse_args(argv)
    s = draw(pd.read_parquet(EVENTS), a.seed)
    if OUT.exists() and not a.force:
        old = pd.read_csv(OUT, dtype=str, keep_default_na=False)
        if (old["label"] != "").any():
            print(f"{OUT} already has labels; not overwriting. Sample hash {id_hash(s.event_id)}")
            return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    s.to_csv(OUT, index=False, encoding="utf-8")
    print(f"wrote {len(s)} rows to {OUT}; source counts {s.source.value_counts().to_dict()}; "
          f"event_id hash {id_hash(s.event_id)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
