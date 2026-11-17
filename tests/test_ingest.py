import io
import json
import zipfile

import pytest

from fda_recall import ingest


def make_zip(n: int) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.json", json.dumps({"results": [{"recall_number": str(i)} for i in range(n)]}))
    return buf.getvalue()


class Resp:
    def __init__(self, js=None, content=b""):
        self._js, self.content = js, content

    def raise_for_status(self):
        pass

    def json(self):
        return self._js


class FakeSession:
    def __init__(self, n=3):
        self.zip, self.n, self.calls = make_zip(n), n, []

    def get(self, url, **kw):
        self.calls.append(url)
        if url == ingest.DOWNLOAD_INDEX:
            return Resp({"results": {"drug": {"enforcement": {"partitions": [
                {"file": "https://example.test/drug-enforcement-0001-of-0001.json.zip"}]}}}})
        if url.startswith("https://api.fda.gov/drug/enforcement.json"):
            return Resp({"meta": {"results": {"total": self.n}}})
        return Resp(content=self.zip)


def run(tmp_path, s, **kw):
    return ingest.ingest_endpoint("drug", session=s, raw_dir=tmp_path, today="2026-01-01", **kw)


def test_ingest_writes_file_and_manifest(tmp_path):
    e = run(tmp_path, FakeSession(3))[0]
    m = json.loads((tmp_path / "manifest.json").read_text())
    assert m["files"][0]["rows"] == 3 and e["rows_match_api_total"] is True
    assert m["files"][0]["sha256"] == ingest.sha256_bytes(make_zip(3))
    assert m["files"][0]["retrieved_utc"].endswith("+00:00")
    assert (tmp_path / "drug" / "2026-01-01" / "drug-enforcement-0001-of-0001.json.zip").exists()


def test_idempotent_second_run_skips(tmp_path):
    run(tmp_path, FakeSession())
    s2 = FakeSession()
    assert run(tmp_path, s2) == []
    assert not any(u.startswith("https://example.test") for u in s2.calls)  # no re-download


def test_force_refuses_to_overwrite_same_day(tmp_path):
    run(tmp_path, FakeSession())
    with pytest.raises(FileExistsError):
        run(tmp_path, FakeSession(), force=True)


def test_row_mismatch_is_flagged(tmp_path):
    s = FakeSession(3)
    s.n = 5  # API says 5, file has 3
    s.zip = make_zip(3)
    assert run(tmp_path, s)[0]["rows_match_api_total"] is False
