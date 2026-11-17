"""Keyword/regex baseline classifier (T3.2.1) - what an analyst could build in Excel.

    from fda_recall.classify.rules import RuleClassifier
    RuleClassifier().predict(["Undeclared milk"])  -> ["ALLERGEN"]
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
RULES = ROOT / "data" / "reference" / "keyword_rules.yaml"
TAX = ROOT / "data" / "reference" / "taxonomy.yaml"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip()


class RuleClassifier:
    def __init__(self, rules_path: Path = RULES, tax_path: Path = TAX):
        rules = yaml.safe_load(Path(rules_path).read_text(encoding="utf-8"))["rules"]
        self.priority = yaml.safe_load(Path(tax_path).read_text(encoding="utf-8"))["tie_break_priority"]
        unknown = set(rules) - set(self.priority)
        if unknown:
            raise ValueError(f"rules for unknown categories: {unknown}")
        self.patterns = [(c, re.compile(rules[c])) for c in self.priority if c in rules]

    def matches(self, text: str) -> list[str]:
        t = normalize(text)
        return [c for c, p in self.patterns if p.search(t)]

    def predict_one(self, text: str) -> str:
        m = self.matches(text)
        return m[0] if m else "OTHER"

    def predict(self, texts) -> list[str]:
        return [self.predict_one(t) for t in texts]
