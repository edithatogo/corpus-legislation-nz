from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate
from typer.testing import CliRunner

from nz_legislation_corpus.cli import app
from nz_legislation_corpus.official_gazette import (
    OFFICIAL_GAZETTE_LISTING_URL,
    build_official_gazette_archive,
    build_official_gazette_manifest,
    discover_official_gazette_issue_links,
    normalize_official_gazette_url,
)


def _official_record(
    *,
    artifact_type: str,
    raw_artifact_path: str,
    source_url: str,
    source_local_id: str,
) -> dict[str, object]:
    return {
        "artifact_type": artifact_type,
        "raw_artifact_path": raw_artifact_path,
        "source_url": source_url,
        "retrieved_at": "2026-07-03T00:00:00Z",
        "content_sha256": "a" * 64,
        "rights_note": "Official Gazette public source capture.",
        "source_local_id": source_local_id,
        "coverage_state": "complete",
        "http_metadata": {"status_code": 200, "content_type": "application/pdf"},
        "extraction": {"text_sha256": "b" * 64},
        "provenance": {
            "pipeline_name": "official-gazette",
            "pipeline_version": "0.5.0",
            "source_name": "NZ Gazette official website",
            "source_record_id": source_local_id,
            "source_retrieved_at": "2026-07-03T00:00:00Z",
            "release_version": "0.5.0",
            "release_commit": "9c438df",
            "license_note": "Official Gazette evidence only.",
        },
    }


@pytest.mark.unit
def test_normalize_official_gazette_url_strips_trailing_slash() -> None:
    assert normalize_official_gazette_url("https://gazette.govt.nz/issues/") == (
        "https://gazette.govt.nz/issues"
    )


@pytest.mark.unit
def test_discover_official_gazette_issue_links_normalizes_and_dedupes() -> None:
    html = """
        <html>
          <body>
            <a href="/issues/2026-01-01/">Issue landing</a>
            <a href="/issues/2026-01-01/1.pdf">PDF</a>
            <a href="https://gazette.govt.nz/issues/2026-01-01/1.pdf/">Duplicate</a>
            <a href="https://example.com/ignore">Ignore me</a>
          </body>
        </html>
    """

    links = discover_official_gazette_issue_links(html, base_url=OFFICIAL_GAZETTE_LISTING_URL)

    assert links == [
        "https://gazette.govt.nz/issues/2026-01-01",
        "https://gazette.govt.nz/issues/2026-01-01/1.pdf",
    ]


@pytest.mark.unit
def test_build_official_gazette_manifest_writes_expected_schema(tmp_path: Path) -> None:
    pdf_path = tmp_path / "raw" / "2026-01-01" / "issue-1.pdf"
    html_path = tmp_path / "raw" / "2026-01-01" / "notice-1.html"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.7")
    html_path.write_text("<html><body>notice</body></html>", encoding="utf-8")

    records = [
        _official_record(
            artifact_type="issue_pdf",
            raw_artifact_path=str(pdf_path.relative_to(tmp_path)),
            source_url="https://gazette.govt.nz/issues/2026-01-01/issue-1.pdf/",
            source_local_id="issue-1",
        ),
        _official_record(
            artifact_type="notice_page",
            raw_artifact_path=str(html_path.relative_to(tmp_path)),
            source_url="https://gazette.govt.nz/issues/2026-01-01/notice-1/",
            source_local_id="notice-1",
        ),
    ]
    schema = json.loads(
        (Path.cwd() / "schemas" / "official_gazette_archive_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    manifest_path = tmp_path / "official-manifest.json"

    manifest = build_official_gazette_manifest(
        records, source_listing_url="https://gazette.govt.nz/issues/", output_path=manifest_path
    )
    validate(manifest, schema)

    assert manifest_path.exists()
    assert manifest["source_listing_url"] == "https://gazette.govt.nz/issues"
    assert manifest["artifact_type_counts"] == {"issue_pdf": 1, "notice_page": 1}
    assert manifest["record_count"] == 2
    assert manifest["records"][0]["artifact_type"] == "issue_pdf"
    assert manifest["records"][0]["source_url"].endswith("issue-1.pdf")
    assert manifest["records"][1]["artifact_type"] == "notice_page"
    assert manifest["records"][1]["source_url"].endswith("notice-1")
    assert (
        manifest["content_sha256"]
        == build_official_gazette_manifest(
            records, source_listing_url="https://gazette.govt.nz/issues/"
        )["content_sha256"]
    )


@pytest.mark.unit
def test_official_gazette_archive_cli_writes_bundle_and_manifest(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    records_jsonl = tmp_path / "records.jsonl"
    source_dir.mkdir()
    (source_dir / "issue.pdf").write_bytes(b"%PDF-1.7")
    (source_dir / "notice.html").write_text("<html>notice</html>", encoding="utf-8")
    records = [
        _official_record(
            artifact_type="issue_pdf",
            raw_artifact_path="issue.pdf",
            source_url="https://gazette.govt.nz/issues/2026-01-01/issue-1.pdf",
            source_local_id="issue-1",
        ),
        _official_record(
            artifact_type="notice_page",
            raw_artifact_path="notice.html",
            source_url="https://gazette.govt.nz/issues/2026-01-01/notice-1",
            source_local_id="notice-1",
        ),
    ]
    records_jsonl.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "official-gazette-archive",
            "--records-jsonl",
            str(records_jsonl),
            "--source-dir",
            str(source_dir),
            "--output-dir",
            str(output_dir),
            "--year",
            "2026",
        ],
    )

    assert result.exit_code == 0, result.output
    assert any(
        path.name.endswith(".tar.zst") or path.name.endswith(".tar.gz")
        for path in output_dir.iterdir()
    )
    assert (output_dir / "corpus-legislation-nz-gazette-official-2026.manifest.json").exists()
    assert (
        output_dir / "corpus-legislation-nz-gazette-official-2026.official-manifest.json"
    ).exists()
    assert (
        output_dir / "corpus-legislation-nz-gazette-official-2026.official-evidence.json"
    ).exists()
    assert (output_dir / "corpus-legislation-nz-gazette-official-2026.SHA256SUMS.txt").exists()


@pytest.mark.unit
def test_official_gazette_archive_builder_requires_records(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="No official Gazette records found"):
        build_official_gazette_archive(
            tmp_path / "source",
            tmp_path / "output",
            records_jsonl=tmp_path / "missing.jsonl",
            year="2026",
        )
