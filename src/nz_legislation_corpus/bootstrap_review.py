from __future__ import annotations

from pathlib import Path
from typing import Any

from .source_redundancy import summarize_source_redundancy
from .utils import read_json, read_jsonl, write_json

REQUIRED_ARTIFACTS = (
    "records.jsonl",
    "manifests/validation_report.json",
    "manifests/latest_manifest.json",
    "manifests/coverage_report.json",
    "_state/sync_state.json",
)


def _data_root(root: Path) -> Path:
    if (root / "records.jsonl").exists():
        return root
    return root / "data"


def _warning_texts(sync_state: dict[str, Any]) -> list[str]:
    stats = sync_state.get("last_stats") or {}
    warnings = stats.get("warnings") or []
    return [str(warning) for warning in warnings]


def _records_failed(sync_state: dict[str, Any]) -> int:
    stats = sync_state.get("last_stats") or {}
    value = stats.get("records_failed") or 0
    return int(value)


def _records_deferred(sync_state: dict[str, Any], data_root: Path) -> int:
    stats = sync_state.get("last_stats") or {}
    value = stats.get("records_deferred")
    if value is not None:
        return int(value or 0)
    return len(read_jsonl(data_root / "_state" / "metadata_only_deferred.jsonl"))


def _browser_fallback_warnings(warnings: list[str]) -> list[str]:
    return [
        warning
        for warning in warnings
        if (
            "browser" in warning.lower()
            or "rendered" in warning.lower()
            or "official_website_rendered_html" in warning
        )
        and ("fallback" in warning.lower() or "official_website" in warning)
    ]


def _browser_fallback_provenance(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    provenance_records: list[dict[str, Any]] = []
    for record in records:
        stable_id = str(record.get("stable_id") or record.get("version_id") or "")
        source_redundancy = record.get("source_redundancy")
        if not isinstance(source_redundancy, dict):
            continue
        attempts = source_redundancy.get("attempts") or []
        if not isinstance(attempts, list):
            continue
        for attempt in attempts:
            if not isinstance(attempt, dict):
                continue
            retrieval_method = str(attempt.get("retrieval_method") or attempt.get("method") or "")
            if retrieval_method != "official_website_rendered_html":
                continue
            provenance_records.append(
                {
                    "stable_id": stable_id,
                    "source_url": attempt.get("source_url") or attempt.get("url"),
                    "retrieval_method": retrieval_method,
                    "retrieval_timestamp_utc": attempt.get("retrieval_timestamp_utc")
                    or attempt.get("retrieved_at"),
                    "content_hash": attempt.get("content_hash") or attempt.get("content_sha256"),
                    "previous_failure_reason": attempt.get("previous_failure_reason")
                    or attempt.get("warning")
                    or attempt.get("error"),
                    "confidence": attempt.get("confidence"),
                    "status": attempt.get("status"),
                    "rights_note": attempt.get("rights_note")
                    or (
                        "Official website rendered diagnostics are for manual triage only; "
                        "they are not canonical corpus content."
                    ),
                }
            )
    return provenance_records


def _period_work_id_count(period_context: dict[str, Any]) -> Any:
    period = period_context.get("period")
    if isinstance(period, dict) and "work_id_count" in period:
        return period.get("work_id_count")
    return period_context.get("work_id_count")


def build_full_corpus_bootstrap_review(root: Path) -> dict[str, Any]:
    """Build a deterministic review summary for a full bootstrap artifact."""
    data_root = _data_root(root)
    missing = [artifact for artifact in REQUIRED_ARTIFACTS if not (data_root / artifact).exists()]
    validation = read_json(data_root / "manifests" / "validation_report.json", default={}) or {}
    manifest = read_json(data_root / "manifests" / "latest_manifest.json", default={}) or {}
    coverage = read_json(data_root / "manifests" / "coverage_report.json", default={}) or {}
    sync_state = read_json(data_root / "_state" / "sync_state.json", default={}) or {}
    records = read_jsonl(data_root / "records.jsonl")
    source_redundancy = summarize_source_redundancy(records)
    deferred_metadata = read_jsonl(data_root / "_state" / "metadata_only_deferred.jsonl")

    warnings = _warning_texts(sync_state)
    failed_warnings = [warning for warning in warnings if "failed" in warning.lower()]
    xml_fallback_warnings = [
        warning
        for warning in warnings
        if "xml" in warning.lower() and ("html" in warning.lower() or "fallback" in warning.lower())
    ]
    browser_fallback_warnings = _browser_fallback_warnings(warnings)
    browser_fallback_provenance = _browser_fallback_provenance(records)
    risk_indicators = coverage.get("risk_indicators") or {}
    period_context = read_json(
        root / "generated" / "full-corpus-periods" / "period_context.json",
        default=None,
    )
    records_failed = _records_failed(sync_state)
    records_deferred = _records_deferred(sync_state, data_root)
    validation_ok = bool(validation.get("ok")) if validation else False
    manifest_sha256 = manifest.get("manifest_sha256")
    records_count = len(records)
    manifest_record_count = int(manifest.get("record_count") or 0)
    coverage_record_count = int(coverage.get("record_count") or 0)
    risk_counts = {
        "missing_text_records": int(risk_indicators.get("missing_text_records") or 0),
        "missing_xml_url_records": int(risk_indicators.get("missing_xml_url_records") or 0),
        "ephemeral_identifier_records": int(
            risk_indicators.get("ephemeral_identifier_records") or 0
        ),
    }
    risk_records = sum(risk_counts.values())
    count_mismatch = (
        manifest_record_count != records_count or coverage_record_count != records_count
    )
    period_quality = None
    if isinstance(period_context, dict):
        period_quality = {
            "period_id": period_context.get("period_id"),
            "work_id_count": _period_work_id_count(period_context),
            "record_count": records_count,
            "validation_ok": validation_ok,
            "manifest_sha256": manifest_sha256,
            "records_failed": records_failed,
            "records_deferred": records_deferred,
            "risk_indicators": risk_counts,
            "api_boundary_decision": period_context.get("api_boundary_decision"),
        }

    ok = (
        not missing
        and validation_ok
        and records_failed == 0
        and bool(manifest_sha256)
        and not count_mismatch
        and risk_records == 0
    )
    if period_quality is not None:
        period_quality["ok"] = ok
        period_quality["triage_required"] = not ok

    return {
        "schema_version": "1.0",
        "ok": ok,
        "data_root": data_root.as_posix(),
        "missing_artifacts": missing,
        "records_jsonl_count": records_count,
        "validation_ok": validation_ok,
        "manifest_sha256": manifest_sha256,
        "manifest_record_count": manifest_record_count,
        "coverage_record_count": coverage_record_count,
        "records_failed": records_failed,
        "records_deferred": records_deferred,
        "deferred_metadata_count": len(deferred_metadata),
        "deferred_metadata_stable_ids": [
            str(row.get("stable_id") or "") for row in deferred_metadata[:50]
        ],
        "failed_version_warnings": failed_warnings,
        "warning_count": len(warnings),
        "xml_to_html_fallback_warning_count": len(xml_fallback_warnings),
        "browser_fallback_warning_count": len(browser_fallback_warnings),
        "browser_fallback_warnings": browser_fallback_warnings,
        "browser_fallback_provenance_count": len(browser_fallback_provenance),
        "browser_fallback_provenance": browser_fallback_provenance,
        "risk_indicators": risk_counts,
        "source_redundancy": source_redundancy,
        "period_context": period_context,
        "period_quality": period_quality,
        "triage_required": not ok,
    }


def write_full_corpus_bootstrap_review(root: Path, output_path: Path) -> dict[str, Any]:
    """Write a full bootstrap artifact review report."""
    report = build_full_corpus_bootstrap_review(root)
    write_json(output_path, report)
    return report
