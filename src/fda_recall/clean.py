"""Clean raw openFDA enforcement data -> product-level and event-level tables.

    python -m fda_recall.clean

Grain: product table = one row per recall_number; event table = one row per event_id
(event_id was verified unique across drug and food in T2.1.1/T2.1.3 and is asserted here).
Event rules (documented, see reports/data_quality.md):
  * reason text      = most frequent distinct text among the event's products; tie -> longest.
                       All distinct texts kept in `reason_variants`.
  * classification   = most severe among products (Class I > II > III > Not Yet Classified);
                       `n_classes` records disagreement.
  * dates            = earliest across products.
Invalid dates (unparseable or outside 2000-01-01..today) become NaT and are listed, never repaired.
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .metrics import record_metric

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
REPORT = ROOT / "reports" / "data_quality.md"
DATE_COLS = ["report_date", "recall_initiation_date", "center_classification_date", "termination_date"]
VALID_CLASSES = ["Class I", "Class II", "Class III"]
SEVERITY = {"Class I": 3, "Class II": 2, "Class III": 1, "Not Yet Classified": 0}
MIN_DATE = pd.Timestamp("2000-01-01")


def load_raw(endpoint: str, raw_dir: Path = RAW) -> pd.DataFrame:
    """Load the most recent manifest entry for the endpoint."""
    manifest = json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))
    entries = [e for e in manifest["files"] if e["endpoint"] == endpoint]
    if not entries:
        raise FileNotFoundError(f"no manifest entry for {endpoint}; run fda_recall.ingest")
    latest = max(entries, key=lambda e: e["retrieved_utc"])
    with zipfile.ZipFile(raw_dir / latest["path"]) as z:
        rows = json.loads(io.BytesIO(z.read(z.namelist()[0])).read())["results"]
    df = pd.DataFrame(rows)
    df["source_file"] = latest["path"]
    return df


def parse_dates(s: pd.Series, today: pd.Timestamp | None = None) -> tuple[pd.Series, pd.Series]:
    """Parse YYYYMMDD strings. Returns (datetimes, invalid_raw_values). Blank/NaN are null, not invalid."""
    today = today or pd.Timestamp(date.today())
    raw = s.where(s.notna() & (s.astype(str).str.strip() != ""))
    parsed = pd.to_datetime(raw, format="%Y%m%d", errors="coerce")
    parsed = parsed.where((parsed >= MIN_DATE) & (parsed <= today))
    invalid = raw[raw.notna() & parsed.isna()]
    return parsed, invalid


def normalize_firm(name: str | None) -> str:
    if not isinstance(name, str):
        return ""
    n = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    n = re.sub(r"\b(inc|llc|ltd|corp|corporation|co|company|lp|llp|dba)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def normalize_text(t: str | None) -> str:
    return re.sub(r"\s+", " ", t.lower()).strip() if isinstance(t, str) else ""


def clean_products(raw: pd.DataFrame, today: pd.Timestamp | None = None) -> tuple[pd.DataFrame, dict]:
    df = raw.copy()
    # Some recent rows have a blank or "N/A" recall_number (observed in the 2026-11 bulk file): keep them,
    # flag them, and give a synthetic unique key so product-level uniqueness still holds.
    rn = df["recall_number"].fillna("").astype(str).str.strip()
    df["recall_number_missing"] = rn.isin(["", "N/A"])
    df["recall_number"] = rn.where(~df["recall_number_missing"],
                                   "UNNUMBERED-" + df["event_id"].astype(str) + "-"
                                   + df.groupby(df["event_id"].astype(str)).cumcount().astype(str))
    invalid_dates: dict[str, list] = {}
    for c in DATE_COLS:
        if c in df:
            df[c], bad = parse_dates(df[c], today)
            invalid_dates[c] = [(df.loc[i, "recall_number"], v) for i, v in bad.items()]
    df["classification"] = df["classification"].str.strip()
    df["is_valid_class"] = df["classification"].isin(VALID_CLASSES)
    df["class_severity"] = df["classification"].map(SEVERITY)
    df["voluntary_mandated"] = df["voluntary_mandated"].replace("", "Unknown").fillna("Unknown")
    df["reason_norm"] = df["reason_for_recall"].map(normalize_text)
    df["firm_norm"] = df["recalling_firm"].map(normalize_firm)
    df["report_month"] = df["report_date"].dt.to_period("M").dt.to_timestamp()
    df["lag_days"] = (df["report_date"] - df["recall_initiation_date"]).dt.days
    assert df["recall_number"].is_unique, "recall_number must be unique at product level"
    return df, invalid_dates


def _mode_longest(texts: pd.Series) -> str:
    counts = texts.value_counts()
    top = counts[counts == counts.iloc[0]].index
    return max(top, key=len)


def to_events(prod: pd.DataFrame) -> pd.DataFrame:
    g = prod.groupby("event_id", sort=True)
    ev = pd.DataFrame({
        "product_type": g["product_type"].first(),
        "n_products": g.size(),
        "reason_for_recall": g["reason_for_recall"].agg(_mode_longest),
        "reason_variants": g["reason_for_recall"].agg(lambda s: sorted(set(s))),
        "n_reason_variants": g["reason_for_recall"].nunique(),
        "class_severity": g["class_severity"].max(),
        "n_classes": g["classification"].nunique(),
        "recalling_firm": g["recalling_firm"].agg(lambda s: s.value_counts().index[0]),
        "firm_norm": g["firm_norm"].agg(lambda s: s.value_counts().index[0]),
        "state": g["state"].agg(lambda s: s.value_counts().index[0]),
        "voluntary_mandated": g["voluntary_mandated"].agg(lambda s: s.value_counts().index[0]),
        "report_date": g["report_date"].min(),
        "recall_initiation_date": g["recall_initiation_date"].min(),
        "center_classification_date": g["center_classification_date"].min(),
    }).reset_index()
    inv = {v: k for k, v in SEVERITY.items()}
    ev["classification"] = ev["class_severity"].map(inv)
    ev["reason_norm"] = ev["reason_for_recall"].map(normalize_text)
    ev["report_month"] = ev["report_date"].dt.to_period("M").dt.to_timestamp()
    ev["lag_days"] = (ev["report_date"] - ev["recall_initiation_date"]).dt.days
    assert ev["event_id"].is_unique, "event_id must be unique at event level"
    assert ev["n_products"].sum() == len(prod)
    return ev


def lag_stats(df: pd.DataFrame) -> pd.DataFrame:
    return (df.dropna(subset=["lag_days"]).groupby("product_type")["lag_days"]
            .describe(percentiles=[0.5, 0.75, 0.9])[["count", "50%", "75%", "90%", "max"]])


def build_report(prod: pd.DataFrame, ev: pd.DataFrame, invalid: dict) -> str:
    L = ["# Data Quality Report (T2.1.3)", "",
         f"Generated by `python -m fda_recall.clean` from raw files {sorted(prod.source_file.unique())}.", ""]
    L += ["## Counts", "", "| product_type | product rows | events | mean products/event |", "|---|---|---|---|"]
    for pt, p in prod.groupby("product_type"):
        e = ev[ev.product_type == pt]
        L.append(f"| {pt} | {len(p):,} | {len(e):,} | {len(p)/len(e):.2f} |")
    L += ["", f"Date range (report_date): {prod.report_date.min().date()} to {prod.report_date.max().date()}.", ""]
    L += [f"Rows with blank/'N/A' recall_number: {int(prod.recall_number_missing.sum())} "
          "(kept; synthetic key `UNNUMBERED-<event_id>-<n>`).", ""]
    L += ["## Classification values (product level)", "", prod["classification"].value_counts().to_frame().to_markdown(), ""]
    other = prod.loc[~prod.is_valid_class, "classification"].value_counts()
    L += [f"Rows outside {{Class I, II, III}}: {int(other.sum())} ({ {k: int(v) for k, v in other.items()} }). Kept with severity 0 and flagged.", ""]
    L += ["## Invalid dates (nulled, not repaired)", ""]
    for c, items in invalid.items():
        L.append(f"- `{c}`: {len(items)} {items[:5]}")
    L += ["", "## Null rate per column (product level)", "",
          prod.isna().mean().mul(100).round(2).rename("% null").to_frame().to_markdown(), ""]
    L += ["## Event-level consolidation", "",
          f"- Events with >1 distinct reason text: {int((ev.n_reason_variants > 1).sum()):,} "
          f"({(ev.n_reason_variants > 1).mean():.1%}). Rule: most frequent text, tie -> longest; variants kept.",
          f"- Events whose products have >1 classification: {int((ev.n_classes > 1).sum()):,} "
          f"({(ev.n_classes > 1).mean():.1%}). Rule: most severe class.",
          f"- Distinct normalized reason texts: {ev.reason_norm.nunique():,} for {len(ev):,} events.", ""]
    L += ["## Reporting lag: report_date - recall_initiation_date (days, product level)", "",
          lag_stats(prod).round(1).to_markdown(), "",
          "Negative lags (report before initiation) are kept and counted: "
          f"{int((prod.lag_days < 0).sum())} rows.", ""]
    return "\n".join(L)


def main() -> int:
    raw = pd.concat([load_raw("drug"), load_raw("food")], ignore_index=True)
    prod, invalid = clean_products(raw)
    ev = to_events(prod)
    PROC.mkdir(parents=True, exist_ok=True)
    prod.to_parquet(PROC / "recalls_product.parquet", index=False)
    ev.to_parquet(PROC / "recalls_event.parquet", index=False)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(build_report(prod, ev, invalid), encoding="utf-8")
    src = "fda_recall/clean.py"
    record_metric("data.n_product_rows", int(len(prod)), src)
    record_metric("data.n_events", int(len(ev)), src)
    record_metric("data.report_date_min", str(prod.report_date.min().date()), src)
    record_metric("data.report_date_max", str(prod.report_date.max().date()), src)
    record_metric("data.lag_p90_days", float(np.nanpercentile(prod.lag_days, 90)), src,
                  note="product level, all types; used to truncate alt-date series in T4.2.1")
    print(f"products={len(prod):,} events={len(ev):,} -> {PROC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
