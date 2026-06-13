"""Integration tests for the sync -> validate -> manifest -> coverage pipeline."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import requests

from nz_legislation_corpus.cli import coverage_report_cmd
from nz_legislation_corpus.manifest import build_change_report, build_manifest
from nz_legislation_corpus.normalize import normalize_version_record
from nz_legislation_corpus.utils import write_jsonl
from nz_legislation_corpus.validate import validate_records


@dataclass
class FakeResponse:
    status_code: int
    payload: object | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    content: bytes = b""
    text: str = ""

    def json(self) -> object:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append((method, url))
        return self.responses.pop(0)

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self.request("GET", url, **kwargs)


class FakeDiscoveryClient:
    def __init__(self, works: list[dict[str, Any]] | None = None) -> None:
        self.works = works or [
            {
                "work_id": "act_public_2026_26",
                "title": "Act 2026",
                "legislation_type": "act",
                "legislation_status": "current",
                "latest_matching_version": {"version_id": "act_public_2026_26_en_2026-06-01"},
            },
            {
                "work_id": "bill_government_2025_100",
                "title": "Bill 2025",
                "legislation_type": "bill",
                "legislation_status": "before_parliament",
                "latest_matching_version": {"version_id": "bill_government_2025_100_en_2025-03-15"},
            },
        ]
        self.calls: list[dict[str, Any]] = []

    def iter_search_works(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        self.calls.append(kwargs)
        yield from self.works

    def discover_versions(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        self.calls.append(kwargs)
        for w in self.works:
            _w: dict[str, Any] = w
            yield {
                "title": _w["title"],
                "version_id": _w["latest_matching_version"]["version_id"],
                "work_id": _w["work_id"],
                "legislation_status": _w["legislation_status"],
                "legislation_type": _w["legislation_type"],
                "administering_agencies": ["Example Agency"],
                "formats": [{"type": "html", "url": "https://example.invalid/act.html"}],
                "is_latest_version": True,
            }


@pytest.mark.integration
def test_sync_validate_manifest_coverage_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "data"
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("NZ_LEGISLATION_API_KEY", "test-key")

    versions = list(FakeDiscoveryClient().discover_versions())
    records = [
        normalize_version_record(
            v,
            raw_content=b"<xml>test content</xml>",
            raw_content_url="https://example.invalid/act.xml",
            raw_content_type="application/xml",
        )
        for v in versions
    ]
    (output_dir / "raw_xml").mkdir(parents=True)
    write_jsonl(output_dir / "records.jsonl", records)
    assert (output_dir / "records.jsonl").exists()

    schema_path = Path.cwd() / "schemas" / "legislation_record.schema.json"
    report = validate_records(output_dir / "records.jsonl", schema_path=schema_path)
    assert report["ok"] is True, f"Validation failed: {report.get('errors')}"
    assert report["record_count"] == 2

    manifest = build_manifest(output_dir)
    assert manifest["record_count"] == 2
    paths = {f["path"] for f in manifest["files"]}
    assert "records.jsonl" in paths

    change = build_change_report(None, manifest)
    assert change["has_changes"] is True
    assert "records.jsonl" in change["added"]

    coverage_report_cmd()
    manifests_dir = output_dir / "manifests"
    coverage = json.loads((manifests_dir / "coverage_report.json").read_text(encoding="utf-8"))
    assert coverage["record_count"] == 2
    assert coverage["by_type"]["act"] == 1
    assert coverage["by_type"]["bill"] == 1


@pytest.mark.integration
def test_multiple_sync_calls_produce_cumulative_state(tmp_path: Path) -> None:
    output_dir = tmp_path / "data"
    (output_dir / "raw_xml").mkdir(parents=True)
    records_1 = [
        normalize_version_record(
            {
                "title": "Act One",
                "version_id": "act_one_2026_1_en_2026-01-01",
                "work_id": "act_one_2026_1",
                "legislation_status": "current",
                "legislation_type": "act",
                "formats": [{"type": "html", "url": "https://example.invalid/a.html"}],
            }
        )
    ]
    write_jsonl(output_dir / "records.jsonl", records_1)
    manifest_1 = build_manifest(output_dir)
    assert manifest_1["record_count"] == 1

    records_2 = [
        normalize_version_record(
            {
                "title": "Act Two",
                "version_id": "act_two_2026_2_en_2026-02-01",
                "work_id": "act_two_2026_2",
                "legislation_status": "current",
                "legislation_type": "act",
                "formats": [{"type": "html", "url": "https://example.invalid/b.html"}],
            }
        )
    ]
    path = output_dir / "records.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.writelines(json.dumps(r, sort_keys=True) + "\n" for r in records_2)

    manifest_2 = build_manifest(output_dir)
    assert manifest_2["record_count"] == 2
    change = build_change_report(manifest_1, manifest_2)
    assert change["has_changes"] is True


@pytest.mark.integration
def test_sync_with_html_only(tmp_path: Path) -> None:
    output_dir = tmp_path / "data"
    records = [
        normalize_version_record(
            {
                "title": "HTML Only Act",
                "version_id": "act_html_only_1_en_2026-01-01",
                "work_id": "act_html_only_1",
                "legislation_status": "current",
                "legislation_type": "act",
                "formats": [{"type": "html", "url": "https://example.invalid/act.html"}],
            },
            raw_content=b"<html>content</html>",
            raw_content_url="https://example.invalid/act.html",
            raw_content_type="text/html",
        )
    ]
    (output_dir / "raw_xml").mkdir(parents=True)
    write_jsonl(output_dir / "records.jsonl", records)

    manifest = build_manifest(output_dir)
    assert manifest["record_count"] == 1

    schema_path = Path.cwd() / "schemas" / "legislation_record.schema.json"
    report = validate_records(output_dir / "records.jsonl", schema_path=schema_path)
    assert report["ok"] is True
    assert "empty_text" not in report["blocking_error_types"]


@pytest.mark.integration
def test_empty_sync_produces_valid_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "data"
    (output_dir / "raw_xml").mkdir(parents=True)
    write_jsonl(output_dir / "records.jsonl", [])

    manifest = build_manifest(output_dir)
    assert manifest["record_count"] == 0
    # The records.jsonl file exists even if empty, so files list is non-empty
    assert len(manifest["files"]) >= 1

    schema_path = Path.cwd() / "schemas" / "legislation_record.schema.json"
    report = validate_records(output_dir / "records.jsonl", schema_path=schema_path)
    assert report["ok"] is True
    assert report["record_count"] == 0
