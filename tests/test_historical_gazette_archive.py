from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from nz_legislation_corpus.historical_gazette import (
    build_historical_gazette_archive,
    build_historical_gazette_manifest,
    build_historical_gazette_review,
    discover_historical_gazette_year_links,
    export_historical_gazette_source,
    extract_historical_gazette_issue_rows,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "victoria_gazette_2008_sample.html"


def _historical_record(
    *,
    stable_id: str,
    record_kind: str,
    source_local_id: str,
    source_url: str,
    rights_note: str = "Historical Gazette source capture; rights caveats preserved.",
    coverage_state: str = "partial",
    extraction: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "stable_id": stable_id,
        "source_id": "victoria_lexisnexis_gazette",
        "source_name": "Victoria University / LexisNexis historical Gazette archive",
        "source_tier": "historical",
        "record_kind": record_kind,
        "source_url": source_url,
        "retrieval_method": "historical_index_parse",
        "retrieved_at": "2026-07-03T00:00:00Z",
        "content_sha256": "a" * 64,
        "raw_artifact_path": "raw/index/2008.html",
        "rights_note": rights_note,
        "source_local_id": source_local_id,
        "coverage_state": coverage_state,
        "extraction": extraction
        or {
            "historical_year": "2008",
            "issue_number": "071",
            "issue_label": "10-Apr",
            "page_start": 1939,
            "page_end": 1939,
            "row_text": "071 10-Apr p. 1939",
        },
        "http_metadata": {"status_code": 200, "content_type": "text/html"},
        "provenance": {
            "pipeline_name": "historical-gazette",
            "pipeline_version": "1.0.0",
            "source_name": "Victoria University / LexisNexis historical Gazette archive",
            "source_record_id": source_local_id,
            "source_retrieved_at": "2026-07-03T00:00:00Z",
            "release_version": "1.0.0",
            "release_commit": "local-dev",
            "license_note": "Historical Gazette source capture; rights caveats preserved.",
        },
    }


def test_discover_historical_gazette_year_links_normalizes_and_dedupes() -> None:
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    links = discover_historical_gazette_year_links(
        html,
        base_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html",
    )

    assert links == [
        "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/1841.html",
        "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/1842.html",
        "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html",
    ]


def test_extract_historical_gazette_issue_rows_parses_issue_rows() -> None:
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    rows = extract_historical_gazette_issue_rows(
        html,
        year="2008",
        source_index_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html",
    )

    assert len(rows) == 6
    assert rows[0]["stable_id"] == "gazette-victoria-lexisnexis-2008-075"
    assert rows[0]["issue_number"] == "075"
    assert rows[0]["page_start"] == 2075
    assert rows[-1]["stable_id"] == "gazette-victoria-lexisnexis-2008-070"
    assert rows[-1]["page_start"] == 1935


def test_build_historical_gazette_manifest_writes_expected_schema(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw" / "index" / "2008.html"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(FIXTURE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    records = [
        _historical_record(
            stable_id="gazette-victoria-lexisnexis-2008-index",
            record_kind="historical_index",
            source_local_id="2008-index",
            source_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html/",
            extraction={
                "historical_year": "2008",
                "year_links": [
                    "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/1841.html",
                    "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/1842.html",
                ],
                "year_link_count": 2,
                "issue_row_count": 1,
                "retrieval_method": "local-file",
                "access_note": "Historical archive access is bounded.",
                "source_index_url": "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html",
            },
        ),
        _historical_record(
            stable_id="gazette-victoria-lexisnexis-2008-071",
            record_kind="historical_page",
            source_local_id="2008-071",
            source_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html#issue-071",
        ),
    ]
    schema = json.loads(
        (
            Path.cwd() / "schemas" / "historical_gazette_archive_manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    manifest_path = tmp_path / "historical-manifest.json"

    manifest = build_historical_gazette_manifest(
        source_records=records,
        source_year="2008",
        source_index_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html/",
        output_path=manifest_path,
    )

    validate(manifest, schema)

    assert manifest_path.exists()
    assert manifest["source_index_url"] == "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html"
    assert manifest["record_kind_counts"] == {"historical_index": 1, "historical_page": 1}
    assert manifest["index_page_count"] == 1
    assert manifest["issue_row_count"] == 1
    assert manifest["historical_year_counts"] == {"2008": 2}


def test_historical_review_flags_missing_rights_and_year_refs(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw" / "index" / "2008.html"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(FIXTURE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    records = [
        _historical_record(
            stable_id="gazette-victoria-lexisnexis-2008-index",
            record_kind="historical_index",
            source_local_id="2008-index",
            source_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html",
            rights_note="",
            extraction={
                "historical_year": "2008",
                "year_links": [],
                "year_link_count": 0,
                "issue_row_count": 0,
                "retrieval_method": "local-file",
                "access_note": "Historical archive access is bounded.",
                "source_index_url": "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html",
            },
        ),
        _historical_record(
            stable_id="gazette-victoria-lexisnexis-2008-071",
            record_kind="historical_page",
            source_local_id="2008-071",
            source_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html#issue-071",
            extraction={
                "historical_year": "2008",
                "row_text": "071 10-Apr p. 1939",
            },
        ),
    ]
    review = build_historical_gazette_review(
        source_records=records,
        manifest={"manifest_sha256": "c" * 64, "content_sha256": "d" * 64},
        source_records_path=tmp_path / "source_records.jsonl",
        records_path=tmp_path / "records.jsonl",
        raw_index_dir=tmp_path / "raw" / "index",
        state_path=tmp_path / "_state" / "export_state.json",
    )

    assert not review["ok"]
    assert review["missing_rights_count"] == 1
    assert review["missing_year_page_reference_count"] == 1


def test_historical_export_and_archive_smoke(tmp_path: Path) -> None:
    export_dir = tmp_path / "data" / "victoria-lexisnexis-gazette"
    result = export_historical_gazette_source(
        output_dir=export_dir,
        source_year="2008",
        index_html_path=FIXTURE_PATH,
        max_issue_rows=3,
    )

    manifest_schema = json.loads(
        (
            Path.cwd() / "schemas" / "historical_gazette_archive_manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (export_dir / "manifests" / "latest_manifest.json").read_text(encoding="utf-8")
    )
    validate(manifest, manifest_schema)

    assert result["ok"]
    assert result["issue_row_count"] == 3
    assert (export_dir / "source_records.jsonl").exists()
    assert (export_dir / "records.jsonl").exists()
    assert (export_dir / "manifests" / "validation_report.json").exists()
    assert (export_dir / "manifests" / "coverage_report.json").exists()
    assert (export_dir / "_state" / "export_state.json").exists()
    assert result["coverage"]["issue_row_count"] == 3
    assert result["review"]["ok"]

    archive_dir = tmp_path / "dist" / "victoria-lexisnexis-gazette"
    archive = build_historical_gazette_archive(
        export_dir / "raw",
        archive_dir,
        records_jsonl=export_dir / "records.jsonl",
        year="2008",
    )
    assert Path(archive["archive_path"]).exists()
    assert Path(archive["manifest_path"]).exists()
    assert Path(archive["provenance_path"]).exists()
