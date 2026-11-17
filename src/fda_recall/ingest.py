"""Ingest openFDA enforcement data from the bulk-download service (decision: docs/data/openfda-source-notes.md).

    python -m fda_recall.ingest --endpoint drug food [--force]

Raw files are immutable: data/raw/<endpoint>/<retrieval_date>/<file>.zip, with data/raw/manifest.json
recording URL, retrieval timestamp (UTC), row count, sha256. OPENFDA_API_KEY (optional) is only used
for the count check against the API and is never written anywhere.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

DOWNLOAD_INDEX = "https://api.fda.gov/download.json"
API_URL = "https://api.fda.gov/{endpoint}/enforcement.json"
ENDPOINTS = ("drug", "food")
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
MANIFEST = RAW_DIR / "manifest.json"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"files": []}


def bulk_partitions(endpoint: str, session) -> list[dict]:
    """Partitions listed in download.json for <endpoint>/enforcement."""
    info = session.get(DOWNLOAD_INDEX, timeout=60)
    info.raise_for_status()
    return info.json()["results"][endpoint]["enforcement"]["partitions"]


def api_total(endpoint: str, session) -> int:
    params = {"limit": 1}
    key = os.environ.get("OPENFDA_API_KEY")
    if key:
        params["api_key"] = key
    r = session.get(API_URL.format(endpoint=endpoint), params=params, timeout=60)
    r.raise_for_status()
    return int(r.json()["meta"]["results"]["total"])


def count_rows(zip_bytes: bytes) -> int:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        return len(json.loads(z.read(z.namelist()[0]))["results"])


def ingest_endpoint(endpoint: str, session=requests, raw_dir: Path = RAW_DIR,
                    manifest_path: Path | None = None, force: bool = False,
                    today: str | None = None) -> list[dict]:
    manifest_path = manifest_path or raw_dir / "manifest.json"
    manifest = load_manifest(manifest_path)
    today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = []
    existing = {e["url"] for e in manifest["files"] if e["endpoint"] == endpoint
                and (raw_dir / e["path"]).exists()}
    total = api_total(endpoint, session)
    for part in bulk_partitions(endpoint, session):
        url = part["file"]
        if url in existing and not force:
            print(f"[skip] {url} already ingested (use --force to re-download)")
            continue
        resp = session.get(url, timeout=300)
        resp.raise_for_status()
        data = resp.content
        rows = count_rows(data)
        rel = Path(endpoint) / today / Path(url).name
        out = raw_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            raise FileExistsError(f"{out} exists; raw files are immutable (re-run on a new date)")
        out.write_bytes(data)
        entry = {"endpoint": endpoint, "url": url, "path": rel.as_posix(),
                 "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "rows": rows, "sha256": sha256_bytes(data), "api_total_at_retrieval": total,
                 "rows_match_api_total": rows == total}
        manifest["files"].append(entry)
        entries.append(entry)
        print(f"[ok] {endpoint}: {rows} rows (API total {total}) -> {out}")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return entries


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--endpoint", nargs="+", choices=ENDPOINTS, default=list(ENDPOINTS))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    with requests.Session() as s:
        for ep in args.endpoint:
            ingest_endpoint(ep, session=s, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
