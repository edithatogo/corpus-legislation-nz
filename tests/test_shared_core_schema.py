from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_shared_core_schema import failures  # noqa: E402


def _validator() -> Any:
    schema = json.loads((ROOT / "schemas" / "shared_nz_corpus_core.schema.json").read_text())
    return Draft202012Validator(schema)


def _valid_record(corpus_id: str = "corpus-nz-legislation") -> dict[str, Any]:
    return {
        "corpus_id": corpus_id,
        "record_id": "nz-legislation-act-1908-000001",
        "source_id": "nz-legislation:work-1908-1:version-1",
        "jurisdiction": "New Zealand",
        "country": "NZ",
        "document_type": "act",
        "display_title": "Example Act 1908",
        "language": "en",
        "record_schema_version": "1.0",
        "canonical_uri": "https://example.org/corpus-nz-legislation/records/nz-legislation-act-1908-000001",
        "source_url": "https://www.legislation.govt.nz/",
        "source_version": "version-1",
        "effective_date": "1908-01-01",
        "published_date": "1908-01-01",
        "last_modified_date": None,
        "content_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "coverage_status": "partial",
        "rights_note": "Source-derived legislation text is not relicensed by this project.",
        "provenance": {
            "pipeline_name": "corpus-nz-legislation",
            "pipeline_version": "0.5.0",
            "source_name": "New Zealand Legislation",
            "source_record_id": "nz-legislation:work-1908-1:version-1",
            "source_retrieved_at": "2026-06-10T00:00:00Z",
            "release_version": "0.1.0",
            "release_commit": "3196fb4",
            "license_note": "Check source rights and project NOTICE.md before reuse.",
        },
    }


def test_valid_legislation_core_record_passes() -> None:
    _validator().validate(_valid_record())


def test_valid_hansard_core_record_passes() -> None:
    record = _valid_record("corpus-nz-hansard")
    record["record_id"] = "nz-hansard-1854-000001"
    record["source_id"] = "documentsdb:hansard:1854:000001"
    record["document_type"] = "hansard_document"
    record["display_title"] = "Hansard example"
    record["record_schema_version"] = "v1"
    record["canonical_uri"] = "https://example.org/corpus-nz-hansard/records/nz-hansard-1854-000001"
    record["source_url"] = "https://www.parliament.nz/en/pb/hansard-debates/"
    record["source_version"] = "documentsdb-2026-06-08"
    record["rights_note"] = "Hansard source-text provenance is documented in release metadata."
    record["provenance"]["pipeline_name"] = "corpus-nz-hansard"
    record["provenance"]["source_name"] = "New Zealand Parliamentary Debates/Hansard"
    record["provenance"]["source_record_id"] = "documentsdb:hansard:1854:000001"
    record["provenance"]["source_retrieved_at"] = None

    _validator().validate(record)


def test_rejects_wrong_corpus_label() -> None:
    record = _valid_record("nz-legislation")
    errors = list(_validator().iter_errors(record))

    assert any(error.path and error.path[0] == "corpus_id" for error in errors)


def test_rejects_missing_manifest_hash() -> None:
    record = _valid_record()
    del record["manifest_sha256"]
    errors = list(_validator().iter_errors(record))

    assert any("manifest_sha256" in error.message for error in errors)


def test_repository_shared_core_contract_is_consistent() -> None:
    assert failures() == []
