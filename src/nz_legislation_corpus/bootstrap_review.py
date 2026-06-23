from __future__ import annotations

from pathlib import Path
from typing import Any

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


def _period_work_id_count(period_context: dict[str, Any]) -> Any:
    period = period_context.get("period")
    if isinstance(period, dict) and "work_id_count" in period:
        return period.get("work_id_count")
    return period_context.get("work_id_count")


def build_full_corpus_bootstrap_review(root: Path) -> dict[str, Any]:
    """Build a deterministic review summary for a full bootstrap artifact."""
    data_root = _data_root(root)
    missing = [
        artifact for artifact in REQUIRED_ARTIFACTS if not (data_root / artifact).exists()
    ]
    validation = read_json(data_root / "manifests" / "validation_report.json", default={}) or {}
    manifest = read_json(data_root / "manifests" / "latest_manifest.json", default={}) or {}
    coverage = read_json(data_root / "manifests" / "coverage_report.json", default={}) or {}
    sync_state = read_json(data_root / "_state" / "sync_state.json", default={}) or {}
    records = read_jsonl(data_root / "records.jsonl")

    warnings = _warning_texts(sync_state)
    failed_warnings = [warning for warning in warnings if "failed" in warning.lower()]
    xml_fallback_warnings = [
        warning
        for warning in warnings
        if "xml" in warning.lower() and ("html" in warning.lower() or "fallback" in warning.lower())
    ]
    risk_indicators = coverage.get("risk_indicators") or {}
    period_context = read_json(
        root / "generated" / "full-corpus-periods" / "period_context.json",
        default=None,
    )
    records_failed = _records_failed(sync_state)
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
        "failed_version_warnings": failed_warnings,
        "warning_count": len(warnings),
        "xml_to_html_fallback_warning_count": len(xml_fallback_warnings),
        "risk_indicators": risk_counts,
        "period_context": period_context,
        "period_quality": period_quality,
        "triage_required": not ok,
    }


def write_full_corpus_bootstrap_review(root: Path, output_path: Path) -> dict[str, Any]:
    """Write a full bootstrap artifact review report."""
    report = build_full_corpus_bootstrap_review(root)
    write_json(output_path, report)
    return report
