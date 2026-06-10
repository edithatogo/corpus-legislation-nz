from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .schema import RECORD_SCHEMA_VERSION
from .utils import read_jsonl, sha256_text, write_json

REQUIRED_FIELDS = [
    "stable_id",
    "record_schema_version",
    "work_id",
    "version_id",
    "title",
    "jurisdiction",
    "country",
    "source",
    "source_url",
    "legislation_type",
    "text",
    "text_sha256",
    "source_hash",
]


def load_schema(schema_path: Path | None) -> dict[str, Any] | None:
    if not schema_path or not schema_path.exists():
        return None
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_records(
    records_path: Path,
    *,
    schema_path: Path | None = None,
    report_path: Path | None = None,
    allow_empty_text: bool = False,
) -> dict[str, Any]:
    records = read_jsonl(records_path)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema) if schema else None

    stable_ids = Counter(str(r.get("stable_id", "")) for r in records)
    version_ids = Counter(str(r.get("version_id", "")) for r in records if r.get("version_id"))

    for value, count in stable_ids.items():
        if value and count > 1:
            errors.append({"type": "duplicate_stable_id", "stable_id": value, "count": count})
    for value, count in version_ids.items():
        if value and count > 1:
            errors.append({"type": "duplicate_version_id", "version_id": value, "count": count})

    for idx, record in enumerate(records):
        for field in REQUIRED_FIELDS:
            if field not in record or record.get(field) in {None, ""}:
                errors.append({"type": "missing_required_field", "row": idx, "field": field})
        if record.get("record_schema_version") != RECORD_SCHEMA_VERSION:
            errors.append(
                {
                    "type": "record_schema_version_mismatch",
                    "row": idx,
                    "stable_id": record.get("stable_id"),
                    "expected": RECORD_SCHEMA_VERSION,
                    "actual": record.get("record_schema_version"),
                }
            )
        if not allow_empty_text and not str(record.get("text", "")).strip():
            errors.append({"type": "empty_text", "row": idx, "stable_id": record.get("stable_id")})
        expected_hash = sha256_text(str(record.get("text", "")))
        if record.get("text_sha256") and record.get("text_sha256") != expected_hash:
            errors.append(
                {"type": "text_hash_mismatch", "row": idx, "stable_id": record.get("stable_id")}
            )
        if not record.get("xml_url"):
            warnings.append(
                {"type": "missing_xml_url", "row": idx, "stable_id": record.get("stable_id")}
            )
        if record.get("id_is_ephemeral"):
            warnings.append(
                {"type": "ephemeral_identifier", "row": idx, "stable_id": record.get("stable_id")}
            )
        if validator:
            for err in validator.iter_errors(record):
                errors.append(
                    {
                        "type": "schema_error",
                        "row": idx,
                        "path": list(err.path),
                        "message": err.message,
                    }
                )

    report = {
        "schema_version": "1.0",
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "records_path": str(records_path),
        "record_count": len(records),
        "blocking_error_types": sorted({error["type"] for error in errors}),
        "informational_warning_types": sorted({warning["type"] for warning in warnings}),
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }
    if report_path:
        write_json(report_path, report)
    return report
