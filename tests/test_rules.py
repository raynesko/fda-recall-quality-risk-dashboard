import pytest

from fda_recall.classify.rules import RuleClassifier

clf = RuleClassifier()

CASES = [
    ("Undeclared milk", "ALLERGEN"),
    ("Product contains undeclared peanuts and soy.", "ALLERGEN"),
    ("Undeclared sulfites", "ALLERGEN"),
    ("Dietary supplement contains undeclared sildenafil", "UNAPPROVED"),
    ("Marketed Without An Approved NDA/ANDA: product is unapproved", "UNAPPROVED"),
    ("Lack of Assurance of Sterility: compounded sterile preparations", "STERILITY"),
    ("Microbial Contamination of Non-Sterile Products: Burkholderia cepacia", "MICRO"),
    ("Product may be contaminated with Listeria monocytogenes", "MICRO"),
    ("CGMP Deviations: presence of NDMA impurity above acceptable intake", "IMPURITY"),
    ("Failed Impurities/Degradation Specifications", "IMPURITY"),
    ("Elevated levels of lead", "IMPURITY"),
    ("Presence of Particulate Matter: glass particles observed", "FOREIGN"),
    ("Product may contain pieces of metal", "FOREIGN"),
    ("Presence of Foreign Tablets/Capsules: bottle contained another product", "MIXUP"),
    ("Labeling: Label Mix-up", "MIXUP"),
    ("Subpotent Drug: low assay at 12 month stability", "POTENCY"),
    ("Failed Dissolution Specifications", "SPEC_FAIL"),
    ("Defective Delivery System: pump does not dispense", "PACKAGING"),
    ("Product prepared, packed, or held under insanitary conditions", "PROCESS_SANITATION"),
    ("Potential for Clostridium botulinum due to under processing", "PROCESS_SANITATION"),
    ("Labeling: Incorrect or Missing Lot and/or Exp Date", "LABELING"),
    ("CGMP Deviations", "CGMP"),
    ("Recall initiated as a precautionary measure", "OTHER"),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_phrase(text, expected):
    assert clf.predict_one(text) == expected


def test_deterministic():
    texts = [t for t, _ in CASES]
    assert clf.predict(texts) == clf.predict(texts) == RuleClassifier().predict(texts)


def test_priority_order_respected():
    m = clf.matches("Undeclared milk due to label mix-up; CGMP deviations")
    assert m[0] == "ALLERGEN" and {"MIXUP", "LABELING", "CGMP"} <= set(m)
