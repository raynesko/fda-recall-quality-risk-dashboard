import re

import duckdb
import pandas as pd

from fda_recall import clean, model
from tests.test_clean import TODAY, raw_fixture


def star_from_fixture():
    prod, _ = clean.clean_products(raw_fixture(), TODAY)
    ev = clean.to_events(prod)
    return prod, ev, model.build_star(prod, ev)


def test_no_orphan_foreign_keys_and_row_reconciliation():
    prod, ev, t = star_from_fixture()
    fe = t["fact_recall_event"]
    assert len(fe) == len(ev) and fe.event_id.is_unique
    assert fe.report_date_key.isin(t["dim_date"].date_key).all()
    assert fe.recall_initiation_date_key.dropna().isin(t["dim_date"].date_key).all()
    assert fe.firm_key.isin(t["dim_firm"].firm_key).all()
    assert fe.category_id.isna().all()  # null when no classified input is given
    assert t["fact_recall_product"].event_id.isin(fe.event_id).all()
    assert fe.n_products.sum() == len(t["fact_recall_product"]) == len(prod)


def test_dictionary_matches_actual_columns_and_markdown():
    _, _, t = star_from_fixture()
    md = model.render_dictionary()
    for name, df in t.items():
        assert list(df.columns) == list(model.DICTIONARY[name]), name
        section = md.split(f"## {name}")[1].split("## ")[0]
        assert re.findall(r"^\| `(\w+)` \|", section, re.M) == list(df.columns)


def test_duckdb_month_counts_match_pandas(tmp_path):
    _, ev, t = star_from_fixture()
    model.write_star(t, tmp_path)
    q = """select d.month_start, count(*) n from read_parquet('{0}/fact_recall_event.parquet') f
           join read_parquet('{0}/dim_date.parquet') d on f.report_date_key = d.date_key
           group by 1 order by 1""".format(tmp_path.as_posix())
    got = duckdb.sql(q).df()
    exp = ev.groupby("report_month").size().rename("n").reset_index()
    print("duckdb:", got.values.tolist(), "pandas:", exp.values.tolist())
    assert got["n"].tolist() == exp["n"].tolist()
    assert pd.to_datetime(got.month_start).tolist() == exp.report_month.tolist()


def test_category_fk_populated_from_classified():
    prod, _ = clean.clean_products(raw_fixture(), TODAY)
    ev = clean.to_events(prod)
    cls = pd.DataFrame({"event_id": ev.event_id, "category": "ALLERGEN", "method": "rules", "confidence": 0.9})
    cls.loc[cls.index[0], ["category", "method", "confidence"]] = ["UNCLASSIFIED", "unclassified", float("nan")]
    t = model.build_star(prod, ev, cls)
    fe, dc = t["fact_recall_event"], t["dim_category"]
    assert fe.category_id.notna().all() and fe.category_id.isin(dc.category_id).all()
    assert dc.category_id.is_unique and "UNCLASSIFIED" in set(dc.category_id) and len(dc) == 15
    assert (fe.category_method == "unclassified").sum() == 1
