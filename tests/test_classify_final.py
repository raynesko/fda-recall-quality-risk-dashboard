import pandas as pd

from fda_recall.classify.final import UNCLASSIFIED, apply_rules, bucket
from fda_recall.classify.rules import RuleClassifier


def test_bucket():
    assert [bucket(n) for n in (0, 1, 2, 5)] == ["none", "single", "multi", "multi"]


def test_apply_rules_never_forces_other():
    rc = RuleClassifier()
    out = apply_rules(pd.Series(["Undeclared milk", "zzz qqq nothing here", "Lack of assurance of sterility"]), rc)
    assert list(out.category) == ["ALLERGEN", UNCLASSIFIED, "STERILITY"]
    assert list(out.method) == ["rules", "unclassified", "rules"]
    assert out.n_rule_matches.iloc[1] == 0 and (out.category != "OTHER").all()
