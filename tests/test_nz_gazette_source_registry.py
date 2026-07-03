from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "nz_gazette_source_registry.json"
REGISTRY_DOC_PATH = ROOT / "docs" / "nz_gazette_source_registry.md"
RAW_SCHEMA_PATH = ROOT / "schemas" / "nz_gazette_raw_source_record.schema.json"
CANONICAL_SCHEMA_PATH = ROOT / "schemas" / "nz_gazette_canonical_record.schema.json"
REGISTRY_SCHEMA_PATH = ROOT / "schemas" / "nz_gazette_source_registry.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_raw_record() -> dict[str, Any]:
    return {
        "stable_id": "gazette-official-2026-01-01-issue-1",
        "source_id": "official_gazette",
        "source_name": "NZ Gazette official website",
        "source_tier": "official",
        "record_kind": "issue_pdf",
        "source_url": "https://gazette.govt.nz/issues/2026-01-01/1.pdf",
        "retrieval_method": "http-get",
        "retrieved_at": "2026-07-03T00:00:00Z",
        "content_sha256": "a" * 64,
        "raw_artifact_path": "raw/official/2026/issue-1.pdf",
        "rights_note": "Official Gazette source capture is public evidence only.",
        "source_local_id": "issue-2026-01-01-1",
        "coverage_state": "partial",
        "http_metadata": {
            "status_code": 200,
            "content_type": "application/pdf",
            "etag": "\"abc\"",
        },
        "extraction": {
            "text_sha256": "b" * 64,
            "text_path": "derived/text/issue-1.txt",
        },
        "provenance": {
            "pipeline_name": "nz-gazette",
            "pipeline_version": "0.1.0",
            "source_name": "NZ Gazette official website",
            "source_record_id": "issue-2026-01-01-1",
            "source_retrieved_at": "2026-07-03T00:00:00Z",
            "release_version": "0.1.0",
            "release_commit": "28a0624",
            "license_note": "Source-specific rights note preserved.",
        },
    }


def _valid_canonical_record() -> dict[str, Any]:
    return {
        "canonical_id": "gazette-2026-01-01-issue-1",
        "canonical_uri": "https://example.org/corpus-nz-gazette/records/gazette-2026-01-01-issue-1",
        "canonical_source": "official_gazette",
        "supporting_sources": [
            {
                "source_id": "official_gazette",
                "source_record_id": "issue-2026-01-01-1",
                "source_url": "https://gazette.govt.nz/issues/2026-01-01/1.pdf",
                "source_tier": "official",
                "source_manifest_sha256": "c" * 64,
                "content_sha256": "a" * 64,
            }
        ],
        "conflicts": [
            {
                "field_name": "title",
                "candidate_values": ["Gazette Notice", "Gazette Notice (DigitalNZ)"],
                "source_ids": ["official_gazette", "digitalnz_gazette"],
                "resolution_state": "unreviewed",
                "review_note": None,
            }
        ],
        "confidence": "high",
        "normalization_version": "1.0",
        "title": "Gazette Notice",
        "source_url": "https://gazette.govt.nz/issues/2026-01-01/1.pdf",
        "rights_note": "Canonical records remain rights-caveated and reproducible from source manifests.",
        "coverage_state": "partial",
        "historical_only": False,
        "provenance": {
            "pipeline_name": "nz-gazette-canonical-builder",
            "pipeline_version": "0.1.0",
            "comparison_run_id": "gazette-compare-2026-07-03-001",
            "source_manifest_sha256": "d" * 64,
            "release_version": "0.1.0",
            "release_commit": "28a0624",
            "license_note": "Canonical record derived from independent source archives.",
        },
    }


@pytest.mark.unit
def test_registry_document_mentions_required_sources() -> None:
    text = REGISTRY_DOC_PATH.read_text(encoding="utf-8")
    for snippet in (
        "official_gazette",
        "digitalnz_gazette",
        "victoria_lexisnexis_gazette",
        "nzlii_gazette",
        "coverage_matrix",
        "canonical_precedence",
        "Tracks 42",
        "Tracks 47",
    ):
        assert snippet in text


@pytest.mark.unit
def test_registry_json_validates_against_schema() -> None:
    schema = _load_json(REGISTRY_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(_load_json(REGISTRY_PATH))


@pytest.mark.unit
def test_raw_source_schema_validates_sample_record() -> None:
    schema = _load_json(RAW_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(_valid_raw_record())


@pytest.mark.unit
def test_canonical_schema_validates_sample_record() -> None:
    schema = _load_json(CANONICAL_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(_valid_canonical_record())


@pytest.mark.unit
def test_raw_and_canonical_schemas_preserve_provenance_and_rights_fields() -> None:
    raw_schema = _load_json(RAW_SCHEMA_PATH)
    canonical_schema = _load_json(CANONICAL_SCHEMA_PATH)

    for schema in (raw_schema, canonical_schema):
        properties = schema["properties"]
        assert "rights_note" in properties
        assert "provenance" in properties

    canonical_properties = canonical_schema["properties"]
    assert "conflicts" in canonical_properties
    assert "supporting_sources" in canonical_properties


@pytest.mark.unit
def test_registry_contract_canonical_precedence_is_stable() -> None:
    registry = _load_json(REGISTRY_PATH)
    assert registry["canonical_precedence"] == [
        "official_gazette",
        "digitalnz_gazette",
        "victoria_lexisnexis_gazette",
        "nzlii_gazette",
    ]
    assert registry["coverage_dimensions"] == [
        "source_id",
        "year",
        "issue_id",
        "notice_id",
        "page_start",
        "page_end",
        "artifact_type",
        "coverage_state",
    ]

