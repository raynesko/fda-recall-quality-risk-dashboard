"""Star-schema export for BI (Power BI / Tableau) and the generated data dictionary.

    python -m fda_recall.model

Tables (Parquet + CSV in data/processed/star/):
  fact_recall_event    grain: one row per event_id
  fact_recall_product  grain: one row per recall_number (bridge/detail for drill-through)
  dim_date             one row per calendar day 2012-01-01..2026-12-31
  dim_firm             one row per normalized recalling firm
  dim_category         root-cause categories from taxonomy.yaml + UNCLASSIFIED (T3.2.4)
fact_recall_event.category_id comes from data/processed/events_classified.parquet (keyword rules v1);
it is null only if that file has not been produced yet.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
STAR = PROC / "star"
DICT_PATH = ROOT / "docs" / "data" / "data-dictionary.md"

DICTIONARY: dict[str, dict[str, str]] = {
    "fact_recall_event": {
        "event_id": "openFDA event_id (PK). One recall event may cover many products.",
        "product_type": "Drugs or Food (openFDA endpoint).",
        "report_date_key": "FK to dim_date.date_key; date FDA posted the recall in the enforcement report.",
        "report_month": "First day of the report_date month (convenience for monthly series).",
        "recall_initiation_date_key": "FK to dim_date.date_key; null when invalid/missing.",
        "firm_key": "FK to dim_firm.firm_key.",
        "category_id": "FK to dim_category.category_id (keyword rules v1; UNCLASSIFIED when no rule matched).",
        "category_method": "rules or unclassified.",
        "category_confidence": "Gold-set precision of the rule match bucket (single vs multiple matches); null if unclassified.",
        "classification": "Most severe FDA class among the event's products (Class I/II/III/Not Yet Classified).",
        "class_severity": "Ordinal 3=Class I, 2=II, 1=III, 0=Not Yet Classified. Weights are arbitrary - see metric dictionary.",
        "n_products": "Number of product rows (recall_numbers) in the event.",
        "n_reason_variants": "Count of distinct reason_for_recall texts across the event's products.",
        "reason_for_recall": "Event reason text (most frequent variant; tie -> longest).",
        "voluntary_mandated": "Initiation type as recorded by FDA; blank recorded as Unknown.",
        "state": "Recalling firm state (most frequent across products).",
        "lag_days": "report_date minus recall_initiation_date in days; null if initiation date invalid.",
    },
    "fact_recall_product": {
        "recall_number": "FDA recall number (PK). Blank/N-A source values get a synthetic UNNUMBERED-<event>-<n> key.",
        "event_id": "FK to fact_recall_event.event_id.",
        "product_type": "Drugs or Food.",
        "classification": "FDA class of this product row.",
        "status": "Status at the time of classification (openFDA does not update it afterwards).",
        "product_description": "Free-text product description.",
        "product_quantity": "Free-text quantity as reported.",
        "distribution_pattern": "Free-text distribution as reported.",
        "recall_number_missing": "True when the source recall_number was blank or N/A.",
    },
    "dim_date": {
        "date_key": "Integer YYYYMMDD (PK).",
        "date": "Calendar date.",
        "year": "Calendar year.",
        "quarter": "Calendar quarter 1-4.",
        "month": "Month number 1-12.",
        "month_name": "English month name.",
        "month_start": "First day of the month.",
    },
    "dim_firm": {
        "firm_key": "Surrogate key (PK).",
        "firm_norm": "Normalized firm name (lowercase, punctuation and legal suffixes removed).",
        "firm_name": "Most frequent original spelling.",
    },
    "dim_category": {
        "category_id": "Taxonomy category id (PK), plus UNCLASSIFIED for events no rule matched.",
        "category_name": "Display name.",
        "product_scope": "drug, food or both.",
        "tie_break_rank": "Position in taxonomy tie_break_priority (1 = wins ties); 99 for UNCLASSIFIED.",
    },
}


def date_key(s: pd.Series) -> pd.Series:
    return s.dt.strftime("%Y%m%d").astype("Int64").where(s.notna())


TAXONOMY = ROOT / "data" / "reference" / "taxonomy.yaml"
CLASSIFIED = PROC / "events_classified.parquet"


def build_dim_category(tax_path: Path = TAXONOMY) -> pd.DataFrame:
    import yaml
    tax = yaml.safe_load(Path(tax_path).read_text(encoding="utf-8"))
    rank = {c: i + 1 for i, c in enumerate(tax["tie_break_priority"])}
    rows = [(c["id"], c["name"], c["applies_to"], rank[c["id"]]) for c in tax["categories"]]
    rows.append(("UNCLASSIFIED", "Unclassified (no keyword rule matched)", "both", 99))
    return pd.DataFrame(rows, columns=list(DICTIONARY["dim_category"])).astype(
        {"category_id": "string", "category_name": "string", "product_scope": "string"})


def build_star(prod: pd.DataFrame, ev: pd.DataFrame, classified: pd.DataFrame | None = None,
               tax_path: Path = TAXONOMY) -> dict[str, pd.DataFrame]:
    firms = (prod.groupby("firm_norm")["recalling_firm"].agg(lambda s: s.value_counts().index[0])
             .rename("firm_name").reset_index())
    firms.insert(0, "firm_key", range(1, len(firms) + 1))
    d = pd.date_range("2012-01-01", "2026-12-31", freq="D")
    dim_date = pd.DataFrame({"date": d})
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"], dim_date["quarter"], dim_date["month"] = d.year, d.quarter, d.month
    dim_date["month_name"] = d.strftime("%B")
    dim_date["month_start"] = d.to_period("M").to_timestamp()
    dim_date = dim_date[list(DICTIONARY["dim_date"])]

    fe = ev.merge(firms[["firm_key", "firm_norm"]], on="firm_norm", how="left")
    fe["report_date_key"] = date_key(fe["report_date"])
    fe["recall_initiation_date_key"] = date_key(fe["recall_initiation_date"])
    if classified is not None:
        c = classified[["event_id", "category", "method", "confidence"]].rename(columns={
            "category": "category_id", "method": "category_method", "confidence": "category_confidence"})
        fe = fe.merge(c, on="event_id", how="left", validate="one_to_one")
        fe["category_id"] = fe["category_id"].astype("string")
    else:
        fe["category_id"] = pd.Series([pd.NA] * len(fe), dtype="string")
        fe["category_method"] = pd.Series([pd.NA] * len(fe), dtype="string")
        fe["category_confidence"] = float("nan")
    fact_event = fe[list(DICTIONARY["fact_recall_event"])]

    fact_product = prod[list(DICTIONARY["fact_recall_product"])].copy()
    dim_category = build_dim_category(tax_path)
    return {"fact_recall_event": fact_event, "fact_recall_product": fact_product,
            "dim_date": dim_date, "dim_firm": firms[list(DICTIONARY["dim_firm"])],
            "dim_category": dim_category}


def write_star(tables: dict[str, pd.DataFrame], out: Path = STAR) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False)
        df.to_csv(out / f"{name}.csv", index=False, encoding="utf-8-sig")


def render_dictionary() -> str:
    L = ["# Data Dictionary (generated by `python -m fda_recall.model`; do not edit by hand)", ""]
    for table, cols in DICTIONARY.items():
        L += [f"## {table}", "", "| column | description |", "|---|---|"]
        L += [f"| `{c}` | {d} |" for c, d in cols.items()]
        L.append("")
    return "\n".join(L)


def main() -> int:
    prod = pd.read_parquet(PROC / "recalls_product.parquet")
    ev = pd.read_parquet(PROC / "recalls_event.parquet")
    classified = pd.read_parquet(CLASSIFIED) if CLASSIFIED.exists() else None
    tables = build_star(prod, ev, classified)
    fe = tables["fact_recall_event"]
    if classified is not None:
        assert fe["category_id"].notna().all(), "every event must have a category"
        assert fe["category_id"].isin(tables["dim_category"]["category_id"]).all(), "orphan category_id"
    write_star(tables)
    DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DICT_PATH.write_text(render_dictionary(), encoding="utf-8")
    print({k: len(v) for k, v in tables.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
