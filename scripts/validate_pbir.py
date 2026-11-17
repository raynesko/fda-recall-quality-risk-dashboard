"""Validate every PBIP/PBIR JSON file in dashboard/ against its declared Microsoft JSON schema.

    python scripts/validate_pbir.py [dashboard_dir]

Schemas are downloaded on first use from developer.microsoft.com (public) and cached in
.cache/pbir_schemas/ (gitignored). Exit code 1 if any file fails.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "pbir_schemas"


def fetch(uri: str) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (uri.replace("https://", "").replace("/", "_"))
    if not f.exists():
        with urllib.request.urlopen(uri, timeout=30) as r:  # noqa: S310 - fixed public host
            f.write_bytes(r.read())
    return json.loads(f.read_text(encoding="utf-8-sig"))


def retrieve(uri: str) -> Resource:
    return Resource.from_contents(fetch(uri), default_specification=DRAFT7)


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dashboard"
    files = [p for p in base.rglob("*") if p.suffix in (".json", ".pbir", ".pbism", ".pbip")
             and "StaticResources" not in p.parts and p.name != "theme.json" and ".pbi" not in p.parts]
    registry = Registry(retrieve=retrieve)
    bad = 0
    for p in sorted(files):
        doc = json.loads(p.read_text(encoding="utf-8"))
        uri = doc.get("$schema")
        if not uri:
            print(f"SKIP (no $schema) {p.relative_to(base)}")
            continue
        v = Draft7Validator(fetch(uri), registry=registry)
        errs = sorted(v.iter_errors(doc), key=lambda e: list(e.path))
        if errs:
            bad += 1
            print(f"FAIL {p.relative_to(base)}")
            for e in errs[:8]:
                print(f"   at {'/'.join(map(str, e.path)) or '<root>'}: {e.message[:300]}")
        else:
            print(f"ok   {p.relative_to(base)}")
    print(f"{len(files)} files, {bad} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
