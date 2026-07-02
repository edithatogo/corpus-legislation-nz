from __future__ import annotations

import json
from pathlib import Path

import pytest

from nz_legislation_corpus import cli


class FakeNZLegislationClient:
    calls = 0

    def __init__(self, settings):
        self.settings = settings

    def discover_versions(self, **kwargs):
        FakeNZLegislationClient.calls += 1
        limit = kwargs.get("max_works")
        records = [
            {
                "title": "Resume Test Act 2026",
                "version_id": "resume-test-act-2026/latest",
                "work_id": "resume-test-act-2026",
                "legislation_status": "current",
                "legislation_type": "act",
                "administering_agencies": ["Example Agency"],
                "formats": [],
                "is_latest_version": True,
            },
            {
                "title": "Resume Test Regulation 2026",
                "version_id": "resume-test-regulation-2026/latest",
                "work_id": "resume-test-regulation-2026",
                "legislation_status": "current",
                "legislation_type": "secondary_legislation",
                "administering_agencies": ["Example Agency"],
                "formats": [],
                "is_latest_version": True,
            },
        ]
        yield from records[:limit]

    @staticmethod
    def format_url(version, fmt):
        return None


class FakeMixedMetadataOnlyNZLegislationClient:
    def __init__(self, settings):
        self.settings = settings

    def discover_versions(self, **kwargs):
        yield {
            "title": "Usable Test Act 2026",
            "version_id": "usable-test-act-2026/latest",
            "work_id": "usable-test-act-2026",
            "legislation_status": "current",
            "legislation_type": "act",
            "administering_agencies": ["Example Agency"],
            "formats": [{"type": "html", "url": "https://example.invalid/usable.html"}],
            "is_latest_version": True,
        }
        yield {
            "title": "Agency Drafted Test Notice 2026",
            "version_id": "secondary-legislation_agency-drafted_2026_~123_en_2026-01-01",
            "work_id": "secondary-legislation_agency-drafted_2026_~123",
            "legislation_status": "current",
            "legislation_type": "secondary_legislation",
            "administering_agencies": ["Example Agency"],
            "formats": [],
            "is_latest_version": True,
        }

    @staticmethod
    def format_url(version, fmt):
        for item in version.get("formats", []):
            if item["type"] == fmt:
                return item["url"]
        return None

    def download_url(self, url):
        return b"<html><body><h1>Usable Test Act 2026</h1><p>Usable text.</p></body></html>"


class FakeFallbackNZLegislationClient:
    def __init__(self, settings):
        self.settings = settings

    def discover_versions(self, **kwargs):
        yield {
            "title": "Old Local Act 1841",
            "version_id": "act_local_1841_1_en_1841-12-22",
            "work_id": "act_local_1841_1",
            "legislation_status": "not_in_force",
            "legislation_type": "act",
            "administering_agencies": [],
            "formats": [
                {
                    "type": "xml",
                    "url": "https://www.legislation.govt.nz/act/local/1841/1/en/latest.xml",
                },
                {
                    "type": "html",
                    "url": "https://www.legislation.govt.nz/act/local/1841/1/en/latest.html",
                },
            ],
            "is_latest_version": True,
        }

    @staticmethod
    def format_url(version, fmt):
        for item in version.get("formats", []):
            if item["type"] == fmt:
                return item["url"]
        return None

    def download_url(self, url):
        if url.endswith(".xml"):
            raise RuntimeError("404 Client Error: Not Found")
        return b"<html><body><h1>Old Local Act 1841</h1><p>Fallback text.</p></body></html>"


@pytest.mark.unit
def test_sync_preserves_state_between_batches(tmp_path: Path, monkeypatch):
    output_dir = tmp_path / "data"
    seed_path = tmp_path / "seed.txt"
    seed_path.write_text("resume-test-act-2026\nresume-test-regulation-2026\n", encoding="utf-8")
    monkeypatch.setenv("NZ_LEGISLATION_API_KEY", "test-key")
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("NZLC_SEARCH_TERMS", "")
    monkeypatch.setattr(cli, "NZLegislationClient", FakeNZLegislationClient)
    monkeypatch.setattr(cli, "write_partitioned_parquet", lambda records, output_dir: [])
    FakeNZLegislationClient.calls = 0

    cli.sync(
        seed_work_ids=seed_path,
        latest_only=False,
        max_works=1,
        allow_no_search_terms=True,
        replace=False,
        embeddings=False,
    )
    first_state = json.loads(
        (output_dir / "_state" / "sync_state.json").read_text(encoding="utf-8")
    )

    cli.sync(
        seed_work_ids=seed_path,
        latest_only=False,
        max_works=2,
        allow_no_search_terms=True,
        replace=False,
        embeddings=False,
    )
    second_state = json.loads(
        (output_dir / "_state" / "sync_state.json").read_text(encoding="utf-8")
    )

    assert FakeNZLegislationClient.calls == 2
    assert first_state["versions"] == {}
    assert second_state["versions"] == {}
    assert second_state["last_stats"]["records_deferred"] == 2
    assert second_state["last_stats"]["records_added"] == 0


@pytest.mark.unit
def test_sync_defers_metadata_only_records_outside_validated_corpus(tmp_path: Path, monkeypatch):
    output_dir = tmp_path / "data"
    seed_path = tmp_path / "seed.txt"
    seed_path.write_text(
        "usable-test-act-2026\nsecondary-legislation_agency-drafted_2026_~123\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NZ_LEGISLATION_API_KEY", "test-key")
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("NZLC_SEARCH_TERMS", "")
    monkeypatch.setattr(cli, "NZLegislationClient", FakeMixedMetadataOnlyNZLegislationClient)
    monkeypatch.setattr(cli, "write_partitioned_parquet", lambda records, output_dir: [])

    cli.sync(
        seed_work_ids=seed_path,
        latest_only=False,
        max_works=None,
        allow_no_search_terms=True,
        replace=False,
        embeddings=False,
    )

    rows = [
        json.loads(line)
        for line in (output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    deferred = [
        json.loads(line)
        for line in (output_dir / "_state" / "metadata_only_deferred.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    state = json.loads((output_dir / "_state" / "sync_state.json").read_text(encoding="utf-8"))

    assert [row["stable_id"] for row in rows] == ["usable-test-act-2026/latest"]
    assert len(deferred) == 1
    assert deferred[0]["stable_id"] == (
        "secondary-legislation_agency-drafted_2026_~123_en_2026-01-01"
    )
    assert deferred[0]["reason"] == "metadata_only_no_downloadable_format"
    assert state["last_stats"]["records_added"] == 1
    assert state["last_stats"]["records_deferred"] == 1
    assert state["last_stats"]["records_failed"] == 0


@pytest.mark.unit
def test_sync_falls_back_to_html_when_xml_404s(tmp_path: Path, monkeypatch):
    output_dir = tmp_path / "data"
    seed_path = tmp_path / "seed.txt"
    seed_path.write_text("act_local_1841_1\n", encoding="utf-8")
    monkeypatch.setenv("NZ_LEGISLATION_API_KEY", "test-key")
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("NZLC_SEARCH_TERMS", "")
    monkeypatch.setattr(cli, "NZLegislationClient", FakeFallbackNZLegislationClient)
    monkeypatch.setattr(cli, "write_partitioned_parquet", lambda records, output_dir: [])

    cli.sync(
        seed_work_ids=seed_path,
        latest_only=False,
        max_works=None,
        allow_no_search_terms=True,
        replace=False,
        embeddings=False,
    )

    rows = [
        json.loads(line)
        for line in (output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    state = json.loads((output_dir / "_state" / "sync_state.json").read_text(encoding="utf-8"))

    assert len(rows) == 1
    assert rows[0]["stable_id"] == "act_local_1841_1_en_1841-12-22"
    assert rows[0]["xml_url"].endswith("latest.xml")
    assert rows[0]["html_url"].endswith("latest.html")
    assert rows[0]["raw_content_path"].endswith(".html")
    assert rows[0]["raw_xml_sha256"] == ""
    assert rows[0]["raw_content_sha256"]
    assert state["last_stats"]["records_added"] == 1
    assert state["last_stats"]["records_failed"] == 0
    assert "used HTML" in state["last_stats"]["warnings"][0]
