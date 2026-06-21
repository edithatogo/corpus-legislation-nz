from pathlib import Path

import pytest

from nz_legislation_corpus.normalize import normalize_version_record
from nz_legislation_corpus.utils import write_jsonl
from nz_legislation_corpus.validate import validate_records


@pytest.mark.unit
def test_validate_record(tmp_path: Path):
    xml = Path("tests/fixtures/sample_legislation.xml").read_bytes()
    record = normalize_version_record(
        {
            "title": "Sample Act 2026",
            "version_id": "sample-version",
            "work_id": "sample-work",
            "legislation_status": "current",
            "legislation_type": "act",
            "formats": [{"type": "xml", "url": "https://example.invalid/sample.xml"}],
        },
        raw_content=xml,
        raw_content_url="https://example.invalid/sample.xml",
        raw_content_type="application/xml",
    )
    path = tmp_path / "records.jsonl"
    write_jsonl(path, [record])
    report = validate_records(path, schema_path=Path("schemas/legislation_record.schema.json"))
    assert report["ok"]
    assert report["record_schema_version"] == "1.0"


@pytest.mark.unit
def test_validate_html_record_warns_without_xml_url(tmp_path: Path):
    html = Path("tests/fixtures/sample_legislation.html").read_bytes()
    record = normalize_version_record(
        {
            "title": "Sample Regulation 2026",
            "version_id": "sample-regulation-version",
            "work_id": "sample-regulation-work",
            "legislation_status": "current",
            "legislation_type": "secondary_legislation",
            "formats": [{"type": "html", "url": "https://example.invalid/sample.html"}],
        },
        raw_content=html,
        raw_content_url="https://example.invalid/sample.html",
        raw_content_type="text/html",
    )
    path = tmp_path / "records.jsonl"
    write_jsonl(path, [record])
    report = validate_records(path, schema_path=Path("schemas/legislation_record.schema.json"))
    assert report["ok"]
    assert report["informational_warning_types"] == ["missing_xml_url"]


@pytest.mark.unit
def test_validate_missing_text_blocks_upload(tmp_path: Path):
    record = normalize_version_record(
        {
            "title": "Metadata Only Notice 2026",
            "version_id": "metadata-only-notice",
            "work_id": "metadata-only-work",
            "legislation_status": "current",
            "legislation_type": "notice",
            "formats": [],
        }
    )
    path = tmp_path / "records.jsonl"
    write_jsonl(path, [record])
    report = validate_records(path, schema_path=Path("schemas/legislation_record.schema.json"))
    assert not report["ok"]
    assert "empty_text" in report["blocking_error_types"]
    assert "missing_xml_url" in report["informational_warning_types"]


@pytest.mark.unit
def test_ephemeral_identifier_flagged():
    from nz_legislation_corpus.normalize import normalize_version_record

    record = normalize_version_record(
        {
            "version_id": "secondary-legislation_pco-drafted_~2026_1_en_~2026-01-01",
            "work_id": "secondary-legislation_pco-drafted_~2026_1",
            "title": "T",
        }
    )
    assert record["id_is_ephemeral"] is True
    assert "~" in record["id_ephemeral_reason"]


@pytest.mark.unit
def test_year_prefers_structured_identifier_over_title_target_year():
    record = normalize_version_record(
        {
            "title": "Climate Change Response (2050 Target and Other Matters) Amendment Act 2025",
            "version_id": "act_public_2025_80_en_2025-12-16",
            "work_id": "act_public_2025_80",
            "legislation_status": "in_force",
            "legislation_type": "act",
            "formats": [],
        }
    )

    assert record["year"] == 2025


@pytest.mark.unit
def test_validate_ephemeral_identifier_is_informational(tmp_path: Path):
    xml = Path("tests/fixtures/sample_legislation.xml").read_bytes()
    record = normalize_version_record(
        {
            "title": "Ephemeral Sample 2026",
            "version_id": "secondary-legislation_pco-drafted_~2026_1_en_~2026-01-01",
            "work_id": "secondary-legislation_pco-drafted_~2026_1",
            "legislation_status": "current",
            "legislation_type": "secondary_legislation",
            "formats": [{"type": "xml", "url": "https://example.invalid/sample.xml"}],
        },
        raw_content=xml,
        raw_content_url="https://example.invalid/sample.xml",
        raw_content_type="application/xml",
    )
    path = tmp_path / "records.jsonl"
    write_jsonl(path, [record])
    report = validate_records(path, schema_path=Path("schemas/legislation_record.schema.json"))
    assert report["ok"]
    assert "ephemeral_identifier" in report["informational_warning_types"]


@pytest.mark.unit
def test_hf_upload_stops_before_remote_calls_on_validation_failure(tmp_path: Path, monkeypatch):
    from nz_legislation_corpus import cli, hf_sync

    record = normalize_version_record(
        {
            "title": "Metadata Only Notice 2026",
            "version_id": "metadata-only-notice",
            "work_id": "metadata-only-work",
            "legislation_status": "current",
            "legislation_type": "notice",
            "formats": [],
        }
    )
    write_jsonl(tmp_path / "records.jsonl", [record])
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("HF_REPO_ID", "owner/dataset")
    monkeypatch.setenv("HF_TOKEN", "token")
    calls: list[str] = []
    monkeypatch.setattr(
        hf_sync, "create_dataset_repo_if_needed", lambda *args, **kwargs: calls.append("create")
    )
    monkeypatch.setattr(
        hf_sync, "upload_large_folder", lambda *args, **kwargs: calls.append("upload")
    )

    try:
        cli.hf_upload_cmd()
    except RuntimeError as exc:
        assert "Blocking validation failures" in str(exc)
    else:
        raise AssertionError("hf-upload should fail validation before remote calls")

    assert calls == []
    assert (tmp_path / "manifests" / "validation_report.json").exists()
