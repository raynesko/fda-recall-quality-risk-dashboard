import json

import pandas as pd
import pytest

from fda_recall import clean, metrics


def raw_fixture():
    base = dict(product_type="Food", state="NJ", voluntary_mandated="", source_file="x",
                center_classification_date="20200105", termination_date=None,
                status="Terminated", product_description="p", product_quantity="1", distribution_pattern="NJ")
    rows = [
        dict(recall_number="F-1", event_id="1", classification="Class II", reason_for_recall="Salmonella",
             recalling_firm="Acme, Inc.", report_date="20200110", recall_initiation_date="20200101", **base),
        dict(recall_number="F-2", event_id="1", classification="Class I", reason_for_recall="Salmonella",
             recalling_firm="Acme Inc", report_date="20200110", recall_initiation_date="20200101", **base),
        dict(recall_number="F-3", event_id="1", classification="Class I", reason_for_recall="Salmonella contamination found",
             recalling_firm="Acme Inc", report_date="20200110", recall_initiation_date="20200101", **base),
        dict(recall_number="F-4", event_id="2", classification="Not Yet Classified", reason_for_recall="Undeclared milk",
             recalling_firm="Bob LLC", report_date="20200201", recall_initiation_date="02121207", **base),
    ]
    return pd.DataFrame(rows)


TODAY = pd.Timestamp("2026-01-01")


def test_parse_dates_flags_invalid_not_null():
    s = pd.Series(["20200110", "02121207", "", None, "20300101"])
    out, bad = clean.parse_dates(s, TODAY)
    assert out.notna().sum() == 1
    assert sorted(bad.tolist()) == ["02121207", "20300101"]  # blank/None are null, not invalid


def test_product_unique_and_classes():
    prod, invalid = clean.clean_products(raw_fixture(), TODAY)
    assert prod.recall_number.is_unique
    assert prod.loc[prod.recall_number == "F-4", "is_valid_class"].item() is False
    assert invalid["recall_initiation_date"] == [("F-4", "02121207")]
    assert invalid["report_date"] == []  # 0 parse failures in dates that matter
    assert (prod.voluntary_mandated == "Unknown").all()


def test_missing_recall_numbers_get_unique_keys():
    r = raw_fixture()
    r.loc[0, "recall_number"] = ""
    r.loc[1, "recall_number"] = "N/A"
    prod, _ = clean.clean_products(r, TODAY)
    assert prod.recall_number.is_unique and prod.recall_number_missing.sum() == 2
    assert prod.recall_number.str.startswith("UNNUMBERED-1-").sum() == 2


def test_duplicate_recall_number_rejected():
    r = raw_fixture()
    r.loc[1, "recall_number"] = "F-1"
    with pytest.raises(AssertionError):
        clean.clean_products(r, TODAY)


def test_event_rules():
    prod, _ = clean.clean_products(raw_fixture(), TODAY)
    ev = clean.to_events(prod).set_index("event_id")
    assert ev.loc["1", "n_products"] == 3
    assert ev.loc["1", "reason_for_recall"] == "Salmonella"  # most frequent (2 of 3 distinct? 2 vs 1)
    assert ev.loc["1", "classification"] == "Class I" and ev.loc["1", "n_classes"] == 2
    assert ev.loc["1", "n_reason_variants"] == 2
    assert ev["n_products"].sum() == len(prod)


def test_tie_prefers_longest():
    assert clean._mode_longest(pd.Series(["a", "abc"])) == "abc"


def test_firm_normalization():
    assert clean.normalize_firm("Acme, Inc.") == clean.normalize_firm("ACME INC") == "acme"


def test_record_metric_roundtrip(tmp_path):
    p = tmp_path / "m.json"
    metrics.record_metric("clf.macro_f1", 0.8, "t", label="target", path=p)
    d = json.loads(p.read_text())
    assert d["clf.macro_f1"]["label"] == "target" and d["clf.macro_f1"]["value"] == 0.8
    assert d["clf.macro_f1"]["source"] == "t" and d["clf.macro_f1"]["recorded_utc"]
    with pytest.raises(ValueError):
        metrics.record_metric("clf.x", 1, "t", label="maybe", path=p)
