"""Validate the shared NZ corpus core schema contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "shared_nz_corpus_core.schema.json"
DOC_PATH = ROOT / "docs" / "shared_nz_corpus_core_schema.md"
TRACK_SPEC_PATH = (
    ROOT / "conductor" / "tracks" / "track_29_shared_nz_corpus_core_schema" / "spec.md"
)

REQUIRED_FIELDS = (
    "corpus_id",
    "record_id",
    "source_id",
    "jurisdiction",
    "country",
    "document_type",
    "display_title",
    "language",
    "record_schema_version",
    "canonical_uri",
    "source_url",
    "source_version",
    "effective_date",
    "published_date",
    "last_modified_date",
    "content_sha256",
    "manifest_sha256",
    "coverage_status",
    "rights_note",
    "provenance",
)

REQUIRED_PROVENANCE_FIELDS = (
    "pipeline_name",
    "pipeline_version",
    "source_name",
    "source_record_id",
    "source_retrieved_at",
    "release_version",
    "release_commit",
    "license_note",
)

REQUIRED_DOC_SNIPPETS = (
    "corpus-nz-legislation",
    "corpus-nz-hansard",
    "GitHub",
    "Hugging Face",
    "Zenodo",
    "OSF",
    "Future metadata",
    "existing GitHub, Hugging Face, and Zenodo URLs",
    "generated endpoint",
)

REQUIRED_TRACK_SNIPPETS = (
    "docs/shared_nz_corpus_core_schema.md",
    "schemas/shared_nz_corpus_core.schema.json",
    "scripts/check_shared_core_schema.py",
    "tests/test_shared_core_schema.py",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _load_schema() -> dict[str, Any]:
    return json.loads(_read_text(SCHEMA_PATH))


def failures() -> list[str]:
    found: list[str] = []

    try:
        schema = _load_schema()
    except (json.JSONDecodeError, OSError) as exc:
        return [f"Shared core schema cannot be loaded: {exc}"]

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema exposes multiple validation subclasses.
        found.append(f"Shared core schema is not a valid Draft 2020-12 schema: {exc}")

    required = set(schema.get("required", []))
    for field in REQUIRED_FIELDS:
        if field not in required:
            found.append(f"Shared core schema does not require {field}.")

    properties = schema.get("properties", {})
    corpus_enum = properties.get("corpus_id", {}).get("enum", [])
    for corpus_id in ("corpus-nz-legislation", "corpus-nz-hansard"):
        if corpus_id not in corpus_enum:
            found.append(f"Shared core schema corpus_id does not allow {corpus_id}.")

    doc_types = properties.get("document_type", {}).get("enum", [])
    for document_type in ("act", "bill", "secondary_legislation", "hansard_document"):
        if document_type not in doc_types:
            found.append(f"Shared core schema document_type does not allow {document_type}.")

    provenance_required = set(properties.get("provenance", {}).get("required", []))
    for field in REQUIRED_PROVENANCE_FIELDS:
        if field not in provenance_required:
            found.append(f"Shared core schema provenance does not require {field}.")

    docs = _read_text(DOC_PATH) if DOC_PATH.exists() else ""
    if not docs:
        found.append("Shared core schema documentation is missing.")
    for snippet in REQUIRED_DOC_SNIPPETS:
        if snippet not in docs:
            found.append(f"Shared core schema documentation is missing: {snippet}")

    track_spec = _read_text(TRACK_SPEC_PATH) if TRACK_SPEC_PATH.exists() else ""
    if not track_spec:
        found.append("Shared core schema track evidence is missing.")
    for snippet in REQUIRED_TRACK_SNIPPETS:
        if snippet not in track_spec:
            found.append(f"Shared core schema track evidence is missing: {snippet}")

    return found


def main() -> int:
    found = failures()
    if found:
        for failure in found:
            print(f"SHARED-CORE-SCHEMA: {failure}")
        return 1
    print("Shared NZ corpus core schema contract is consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
