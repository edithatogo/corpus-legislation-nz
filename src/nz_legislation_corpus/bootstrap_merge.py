from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .manifest import build_manifest
from .parquet_writer import write_partitioned_parquet
from .schema import RECORD_SCHEMA_VERSION
from .utils import read_json, read_jsonl, utc_now_iso, write_json, write_jsonl
from .validate import validate_records


def _data_root(path: Path) -> Path:
    path = Path(path)
    if (path / "records.jsonl").exists():
        return path
    return path / "data"


def _copy_tree_contents(source: Path, destination: Path) -> int:
    if not source.exists():
        return 0
    count = 0
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != path.read_bytes():
            shutil.copy2(path, target)
        count += 1
    return count


def _merge_sync_states(states: list[dict[str, Any]]) -> dict[str, Any]:
    versions: dict[str, str] = {}
    warnings: list[str] = []
    totals: dict[str, Any] = {
        "works_checked": 0,
        "versions_checked": 0,
        "records_added": 0,
        "records_changed": 0,
        "records_unchanged": 0,
        "records_failed": 0,
        "parquet_files_written": 0,
    }
    for state in states:
        versions.update({str(k): str(v) for k, v in (state.get("versions") or {}).items()})
        stats = state.get("last_stats") or {}
        for key in totals:
            totals[key] += int(stats.get(key) or 0)
        warnings.extend(str(w) for w in stats.get("warnings") or [])

    totals["warnings"] = sorted(set(warnings))
    return {
        "schema_version": "1.0",
        "merged_at_utc": utc_now_iso(),
        "versions": dict(sorted(versions.items())),
        "last_stats": totals,
        "records_changed_on_disk": True,
    }


def build_coverage_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_year: dict[str, int] = {}
    missing_text = 0
    missing_xml = 0
    ephemeral_ids = 0
    for record in records:
        by_type[str(record.get("legislation_type") or "unknown")] = (
            by_type.get(str(record.get("legislation_type") or "unknown"), 0) + 1
        )
        by_status[str(record.get("legislation_status") or "unknown")] = (
            by_status.get(str(record.get("legislation_status") or "unknown"), 0) + 1
        )
        by_year[str(record.get("year") or "unknown")] = (
            by_year.get(str(record.get("year") or "unknown"), 0) + 1
        )
        if not str(record.get("text") or "").strip():
            missing_text += 1
        if not str(record.get("xml_url") or "").strip():
            missing_xml += 1
        if record.get("id_is_ephemeral"):
            ephemeral_ids += 1
    return {
        "schema_version": "1.0",
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "record_count": len(records),
        "by_type": dict(sorted(by_type.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_year": dict(sorted(by_year.items())),
        "risk_indicators": {
            "missing_text_records": missing_text,
            "missing_xml_url_records": missing_xml,
            "ephemeral_identifier_records": ephemeral_ids,
        },
        "recommendation": (
            "Review merged shard provenance, failed-version state, and reconciliation "
            "evidence before claiming corpus completeness."
            if records
            else "No records found."
        ),
    }


def merge_bootstrap_artifacts(
    artifact_roots: list[Path],
    output_dir: Path,
    *,
    schema_path: Path = Path("schemas/legislation_record.schema.json"),
) -> dict[str, Any]:
    if not artifact_roots:
        raise ValueError("At least one artifact root is required")

    records_by_id: dict[str, dict[str, Any]] = {}
    sync_states: list[dict[str, Any]] = []
    artifact_summaries: list[dict[str, Any]] = []
    raw_file_count = 0

    for artifact_root in artifact_roots:
        data_root = _data_root(artifact_root)
        records = read_jsonl(data_root / "records.jsonl")
        if not records:
            raise ValueError(f"No records found in artifact: {artifact_root}")
        for record in records:
            stable_id = str(record.get("stable_id") or "")
            if not stable_id:
                raise ValueError(f"Record without stable_id in artifact: {artifact_root}")
            records_by_id[stable_id] = record
        state = read_json(data_root / "_state" / "sync_state.json", default={}) or {}
        if state:
            sync_states.append(state)
        raw_file_count += _copy_tree_contents(data_root / "raw_xml", output_dir / "raw_xml")
        artifact_summaries.append(
            {
                "artifact_root": artifact_root.as_posix(),
                "records_jsonl_count": len(records),
                "sync_state_present": bool(state),
            }
        )

    merged_records = sorted(records_by_id.values(), key=lambda r: str(r.get("stable_id", "")))
    write_jsonl(output_dir / "records.jsonl", merged_records)
    write_partitioned_parquet(merged_records, output_dir / "parquet")
    write_json(output_dir / "_state" / "sync_state.json", _merge_sync_states(sync_states))

    validation = validate_records(output_dir / "records.jsonl", schema_path=schema_path)
    write_json(output_dir / "manifests" / "validation_report.json", validation)
    previous_manifest = read_json(output_dir / "manifests" / "latest_manifest.json", default=None)
    manifest = build_manifest(
        output_dir, manifest_path=output_dir / "manifests" / "latest_manifest.json"
    )
    if previous_manifest:
        from .manifest import build_change_report

        write_json(
            output_dir / "manifests" / "latest_changes.json",
            build_change_report(previous_manifest, manifest),
        )
    coverage = build_coverage_report(merged_records)
    write_json(output_dir / "manifests" / "coverage_report.json", coverage)

    report = {
        "schema_version": "1.0",
        "merged_at_utc": utc_now_iso(),
        "artifact_count": len(artifact_roots),
        "artifact_roots": artifact_summaries,
        "record_count": len(merged_records),
        "raw_file_count": raw_file_count,
        "validation_ok": validation.get("ok") is True,
        "manifest_sha256": manifest.get("manifest_sha256"),
        "coverage_record_count": coverage["record_count"],
        "output_dir": output_dir.as_posix(),
    }
    write_json(output_dir / "manifests" / "bootstrap_merge_report.json", report)
    return report
