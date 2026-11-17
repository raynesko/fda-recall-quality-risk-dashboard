
import pandas as pd
import pytest

from fda_recall.labeling import label, sample

EVENTS = sample.EVENTS
GOLD = sample.OUT
needs_data = pytest.mark.skipif(not EVENTS.exists(), reason="processed data not built")


@needs_data
def test_sample_reproducible_and_matches_file():
    ev = pd.read_parquet(EVENTS)
    a, b = sample.draw(ev, 42), sample.draw(ev, 42)
    assert sample.id_hash(a.event_id) == sample.id_hash(b.event_id)
    assert len(a) == 300 and a.event_id.is_unique
    assert a.source.value_counts().to_dict() == {"random": 200, "targeted": 100}
    if GOLD.exists():
        gold = pd.read_csv(GOLD, dtype=str, keep_default_na=False)
        assert sample.id_hash(gold.event_id) == sample.id_hash(a.event_id)


def test_alloc_sums_exactly():
    s = pd.Series({"a": 10, "b": 33, "c": 57})
    assert sample._alloc(s, 200).sum() == 200


@needs_data
def test_gold_labels_valid():
    if not GOLD.exists():
        pytest.skip("gold set not drawn")
    gold = pd.read_csv(GOLD, dtype=str, keep_default_na=False)
    assert list(gold.columns) == sample.COLUMNS
    assert label.validate(gold, label.load_categories()) == []


def test_validate_flags_unknown_label():
    df = pd.DataFrame({"event_id": ["1", "2"], "label": ["MICRO", "NOPE"], "secondary_label": ["", ""]})
    assert label.validate(df, label.load_categories()) == ["2: unknown label NOPE"]
