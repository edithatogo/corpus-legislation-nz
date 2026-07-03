from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .archive import build_archive
from .artifact_provenance import build_release_evidence
from .utils import (
    read_json,
    read_jsonl,
    sha256_file,
    sha256_text,
    utc_now_iso,
    write_json,
    write_jsonl,
)

CANONICAL_ARCHIVE_PREFIX = "corpus-legislation-nz-gazette-canonical"
CANONICAL_BUILDER_VERSION = "1.0.0"
CANONICAL_RELEASE_COMMIT = "0000000"
CANONICAL_URI_PREFIX = "https://github.com/edithatogo/corpus-legislation-nz/canonical/gazette"
DEFAULT_COMPARISON_RUN_ID = "gazette-compare-local"
SOURCE_PRECEDENCE = (
    "official_gazette",
    "digitalnz_gazette",
    "victoria_lexisnexis_gazette",
    "nzlii_gazette",
)
_TEXT_HASH_FIELDS = (
    "normalized_text_sha256",
    "normalized_sha256",
    "text_sha256",
    "content_text_sha256",
)
_TITLE_FIELDS = ("title", "notice_title", "issue_title", "name")
_DATE_FIELDS = (
    "publication_date",
    "issue_date",
    "date",
    "notice_date",
    "released_at",
)
_PAGE_START_FIELDS = ("page_start", "start_page", "page")
_PAGE_END_FIELDS = ("page_end", "end_page")
_ID_FIELDS = ("notice_id", "issue_id", "work_id", "source_local_id", "stable_id", "version_id")
_SIMILARITY_THRESHOLD = 0.94


def _normalize_text(value: str | None) -> str:
    return re.sub(
        r"[^\w\s-]",
        "",
        re.sub(r"\s+", " ", str(value or "").strip().lower()),
    )


def _first_nonempty(record: Mapping[str, Any], fields: Sequence[str]) -> str:
    for field in fields:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_from_mapping(record: Mapping[str, Any], fields: Sequence[str]) -> str:
    for field in fields:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)) and str(value).strip():
            return str(value)
    extraction = record.get("extraction")
    if isinstance(extraction, Mapping):
        return _extract_from_mapping(extraction, fields)
    return ""


def _extract_page_value(record: Mapping[str, Any], fields: Sequence[str]) -> str:
    value = _extract_from_mapping(record, fields)
    if value:
        return value
    return ""


def _source_record_id(record: Mapping[str, Any]) -> str:
    return _first_nonempty(record, _ID_FIELDS) or _first_nonempty(record, ("id",))


def _source_url(record: Mapping[str, Any]) -> str:
    return _first_nonempty(record, ("source_url", "url", "landing_url"))


def _source_title(record: Mapping[str, Any]) -> str:
    return _extract_from_mapping(record, _TITLE_FIELDS)


def _source_date(record: Mapping[str, Any]) -> str:
    return _extract_from_mapping(record, _DATE_FIELDS)


def _source_page_start(record: Mapping[str, Any]) -> str:
    return _extract_page_value(record, _PAGE_START_FIELDS)


def _source_page_end(record: Mapping[str, Any]) -> str:
    return _extract_page_value(record, _PAGE_END_FIELDS)


def _source_text_hash(record: Mapping[str, Any]) -> str:
    return _extract_from_mapping(record, _TEXT_HASH_FIELDS)


def _source_content_hash(record: Mapping[str, Any]) -> str:
    return _first_nonempty(record, ("content_sha256", "sha256", "source_content_sha256"))


def _comparison_key(record: Mapping[str, Any]) -> tuple[str, str]:
    content_hash = _source_content_hash(record)
    if content_hash:
        return ("content", content_hash)
    text_hash = _source_text_hash(record)
    if text_hash:
        return ("text", text_hash)

    notice_id = _first_nonempty(record, ("notice_id",)) or _extract_from_mapping(record, ("notice_id",))
    issue_id = _first_nonempty(record, ("issue_id",)) or _extract_from_mapping(record, ("issue_id",))
    title = _normalize_text(_source_title(record))
    date = _source_date(record)
    page_start = _source_page_start(record)
    page_end = _source_page_end(record)

    if notice_id and date and page_start:
        return ("notice", "|".join((notice_id, date, page_start, page_end or "", title)))
    if issue_id and date:
        return ("issue", "|".join((issue_id, date, title, page_start, page_end or "")))
    if date and title:
        return ("metadata", "|".join((date, title, page_start, page_end or "")))
    source_id = str(record.get("source_id") or "")
    return ("fallback", "|".join((source_id, _source_record_id(record), title)))


def _fuzzy_group_key(record: Mapping[str, Any]) -> tuple[str, str]:
    """Return an auxiliary key used to detect near matches."""
    title = _normalize_text(_source_title(record))
    date = _source_date(record)
    page = _source_page_start(record)
    source_id = str(record.get("source_id") or "")
    return ("fuzzy", f"{source_id}|{date}|{page}|{title}")


def _load_source_archive(source_dir: Path) -> dict[str, Any]:
    source_dir = Path(source_dir)
    records_path = source_dir / "records.jsonl"
    if not records_path.exists():
        records_path = source_dir / "source_records.jsonl"
    records = read_jsonl(records_path)
    if not records:
        raise RuntimeError(f"No source records found in {records_path}")

    manifest_path = source_dir / "manifests" / "latest_manifest.json"
    if not manifest_path.exists():
        manifests = sorted(source_dir.glob("*.manifest.json"))
        if manifests:
            manifest_path = manifests[0]
    if not manifest_path.exists():
        raise RuntimeError(f"No manifest found in {source_dir}")
    manifest = read_json(manifest_path, default={}) or {}
    source_id = str(manifest.get("source_id") or records[0].get("source_id") or "").strip()
    if not source_id:
        raise RuntimeError(f"Unable to determine source_id for {source_dir}")
    return {
        "source_dir": source_dir,
        "records_path": records_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "source_id": source_id,
        "source_name": str(manifest.get("source_name") or records[0].get("source_name") or source_id),
        "source_tier": str(manifest.get("source_tier") or records[0].get("source_tier") or ""),
        "records": records,
    }


def _load_source_archive_or_missing(source_tree: Mapping[str, Any]) -> dict[str, Any]:
    source_dir = Path(source_tree["source_dir"])
    expected_source_id = str(source_tree.get("source_id") or "").strip()
    expected_source_name = str(source_tree.get("source_name") or "").strip()
    expected_source_tier = str(source_tree.get("source_tier") or "").strip()
    try:
        loaded = _load_source_archive(source_dir)
    except Exception as error:  # noqa: BLE001
        return {
            "source_dir": source_dir,
            "source_id": expected_source_id,
            "source_name": expected_source_name or expected_source_id,
            "source_tier": expected_source_tier,
            "missing": True,
            "missing_reason": str(error),
        }
    loaded["missing"] = False
    return loaded


def _source_manifest_sha256(source: Mapping[str, Any]) -> str:
    manifest = source.get("manifest")
    if isinstance(manifest, Mapping):
        value = str(manifest.get("manifest_sha256") or "").strip()
        if value:
            return value
    manifest_path = Path(source["manifest_path"])
    return sha256_file(manifest_path)


def _precedence_index(source_id: str) -> int:
    try:
        return SOURCE_PRECEDENCE.index(source_id)
    except ValueError:
        return len(SOURCE_PRECEDENCE)


def _supporting_source(record: Mapping[str, Any], source_manifest_sha256: str) -> dict[str, Any]:
    return {
        "source_id": record["source_id"],
        "source_record_id": _source_record_id(record),
        "source_url": _source_url(record),
        "source_tier": record["source_tier"],
        "source_manifest_sha256": source_manifest_sha256,
        "content_sha256": _source_content_hash(record) or sha256_text(
            json.dumps(record, sort_keys=True, ensure_ascii=False)
        ),
    }


def _choose_value(records: Sequence[Mapping[str, Any]], *, fields: Sequence[str]) -> str:
    for record in records:
        value = _extract_from_mapping(record, fields)
        if value:
            return value
    return ""


def _collect_candidates(records: Sequence[Mapping[str, Any]], field_name: str) -> list[str]:
    values: list[str] = []
    if field_name == "title":
        values = [_source_title(record) for record in records if _source_title(record)]
    elif field_name == "source_url":
        values = [_source_url(record) for record in records if _source_url(record)]
    elif field_name == "source_local_id":
        values = [_source_record_id(record) for record in records if _source_record_id(record)]
    elif field_name == "publication_date":
        values = [_source_date(record) for record in records if _source_date(record)]
    elif field_name == "page_start":
        values = [_source_page_start(record) for record in records if _source_page_start(record)]
    elif field_name == "page_end":
        values = [_source_page_end(record) for record in records if _source_page_end(record)]
    elif field_name == "content_sha256":
        values = [_source_content_hash(record) for record in records if _source_content_hash(record)]
    elif field_name == "text_sha256":
        values = [_source_text_hash(record) for record in records if _source_text_hash(record)]
    elif field_name == "rights_note":
        values = [
            str(record.get("rights_note") or "").strip()
            for record in records
            if str(record.get("rights_note") or "").strip()
        ]
    return list(dict.fromkeys(values))


def _conflict_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    conflict_fields = [
        "title",
        "notice_id",
        "issue_id",
        "publication_date",
        "page_start",
        "page_end",
        "content_sha256",
        "text_sha256",
        "rights_note",
    ]
    conflicts: list[dict[str, Any]] = []
    source_ids = [str(record.get("source_id") or "") for record in records if record.get("source_id")]
    for field_name in conflict_fields:
        candidate_values = _collect_candidates(records, field_name)
        if len(candidate_values) < 2:
            continue
        conflicts.append(
            {
                "field_name": field_name,
                "candidate_values": candidate_values,
                "source_ids": list(dict.fromkeys(source_ids)),
                "resolution_state": "unreviewed",
                "review_note": None,
            }
        )
    return conflicts


def _effective_conflicts(
    canonical_id: str,
    conflicts: Sequence[Mapping[str, Any]],
    decisions_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for conflict in conflicts:
        key = (canonical_id, str(conflict["field_name"]))
        conflict_copy = dict(conflict)
        decision = decisions_by_key.get(key)
        if decision:
            selected_value = str(decision.get("selected_value") or "").strip()
            candidate_values = [str(value) for value in conflict_copy["candidate_values"]]
            if selected_value and selected_value in candidate_values:
                conflict_copy["resolution_state"] = str(
                    decision.get("resolution_state") or "reviewed"
                )
                conflict_copy["review_note"] = str(decision.get("rationale") or "")
        resolved.append(conflict_copy)
    return resolved


def _confidence_for_group(records: Sequence[Mapping[str, Any]], conflicts: Sequence[Mapping[str, Any]]) -> str:
    if conflicts:
        return "low"
    source_ids = {str(record.get("source_id") or "") for record in records if record.get("source_id")}
    content_hashes = {_source_content_hash(record) for record in records if _source_content_hash(record)}
    if len(source_ids) >= 2 and len(content_hashes) <= 1:
        return "high"
    if len(source_ids) >= 2:
        return "medium"
    return "medium"


def _coverage_state_for_group(records: Sequence[Mapping[str, Any]]) -> str:
    states = [str(record.get("coverage_state") or "unknown") for record in records]
    for state in ("blocked", "gap", "partial", "complete"):
        if state in states:
            return state
    return "unknown"


def _historical_only(records: Sequence[Mapping[str, Any]]) -> bool:
    source_tiers = {str(record.get("source_tier") or "") for record in records if record.get("source_tier")}
    source_ids = {str(record.get("source_id") or "") for record in records if record.get("source_id")}
    return source_tiers == {"historical"} and bool(source_ids)


def _canonical_source_id(records: Sequence[Mapping[str, Any]]) -> str:
    ordered = sorted(records, key=lambda record: _precedence_index(str(record.get("source_id") or "")))
    return str(ordered[0].get("source_id") or "")


def _canonical_uri(canonical_id: str) -> str:
    return f"{CANONICAL_URI_PREFIX}/{canonical_id}"


def _canonical_id(group_key: tuple[str, str], canonical_source: str, records: Sequence[Mapping[str, Any]]) -> str:
    stable_bits = [
        group_key[0],
        group_key[1],
        canonical_source,
        _normalize_text(_choose_value(records, fields=_TITLE_FIELDS)),
        _choose_value(records, fields=("publication_date", "issue_date", "date", "notice_date")),
    ]
    digest = sha256_text("|".join(bit for bit in stable_bits if bit))
    title_bit = _normalize_text(_choose_value(records, fields=_TITLE_FIELDS))[:24].replace(" ", "-")
    date_bit = _choose_value(records, fields=("publication_date", "issue_date", "date", "notice_date"))[:10]
    prefix = "gazette"
    if date_bit:
        prefix = f"gazette-{date_bit}"
    elif title_bit:
        prefix = f"gazette-{title_bit}"
    return f"{prefix}-{digest[:12]}"


def _archive_output_dir(output_dir: Path) -> Path:
    resolved = Path(output_dir)
    if len(resolved.parents) >= 2:
        return resolved.parents[1] / "dist" / CANONICAL_ARCHIVE_PREFIX
    return resolved.parent / "dist" / CANONICAL_ARCHIVE_PREFIX


def build_nz_gazette_canonical_records(
    source_trees: Sequence[Mapping[str, Any]],
    *,
    decisions: Sequence[Mapping[str, Any]] | None = None,
    comparison_run_id: str = DEFAULT_COMPARISON_RUN_ID,
) -> dict[str, Any]:
    """Compare source archives and build canonical Gazette records."""
    loaded_sources = []
    missing_sources: list[dict[str, Any]] = []
    for source_tree in source_trees:
        loaded = _load_source_archive_or_missing(source_tree)
        if loaded.get("missing"):
            missing_sources.append(
                {
                    "source_id": loaded.get("source_id") or str(source_tree.get("source_id") or ""),
                    "source_name": loaded.get("source_name") or str(source_tree.get("source_name") or ""),
                    "source_tier": loaded.get("source_tier") or str(source_tree.get("source_tier") or ""),
                    "source_dir": str(loaded.get("source_dir") or source_tree.get("source_dir") or ""),
                    "missing_reason": loaded.get("missing_reason") or "missing_source_archive",
                }
            )
            continue
        loaded_sources.append(loaded)

    combined_records: list[dict[str, Any]] = []
    for loaded in loaded_sources:
        source_manifest_sha256 = _source_manifest_sha256(loaded)
        for record in loaded["records"]:
            record = dict(record)
            if not record.get("source_id"):
                record["source_id"] = loaded["source_id"]
            if not record.get("source_name"):
                record["source_name"] = loaded["source_name"]
            if not record.get("source_tier"):
                record["source_tier"] = loaded["source_tier"]
            combined_records.append(
                {
                    "record": record,
                    "source_manifest_sha256": source_manifest_sha256,
                    "source_dir": str(loaded["source_dir"]),
                }
            )

    if not combined_records:
        missing_summary = ", ".join(
            f"{item.get('source_id') or item.get('source_dir')}: {item.get('missing_reason')}"
            for item in missing_sources
        )
        raise RuntimeError(
            "No canonical comparison inputs were available. "
            f"Missing sources: {missing_summary or 'none'}"
        )

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in combined_records:
        grouped[_comparison_key(item["record"])].append(item)

    decisions_by_key = {}
    for decision in decisions or []:
        canonical_id = str(decision.get("canonical_id") or "").strip()
        field_name = str(decision.get("field_name") or "").strip()
        if canonical_id and field_name:
            decisions_by_key[(canonical_id, field_name)] = decision

    canonical_records: list[dict[str, Any]] = []
    conflict_queue: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    matched_count = 0
    unmatched_count = 0
    conflict_count = 0
    historical_only_count = 0
    low_confidence_count = 0
    exact_match_count = 0

    for group_key in sorted(grouped):
        items = grouped[group_key]
        records = [item["record"] for item in items]
        canonical_source = _canonical_source_id(records)
        canonical_id = _canonical_id(group_key, canonical_source, records)
        conflicts = _effective_conflicts(canonical_id, _conflict_records(records), decisions_by_key)
        confidence = _confidence_for_group(records, conflicts)
        coverage_state = _coverage_state_for_group(records)
        historical_only = _historical_only(records)
        if historical_only:
            historical_only_count += 1
        if confidence == "low":
            low_confidence_count += 1
        if len(items) > 1:
            matched_count += 1
            if len({_source_content_hash(record) for record in records if _source_content_hash(record)}) <= 1:
                exact_match_count += 1
        else:
            unmatched_count += 1
        if conflicts:
            conflict_count += 1
            if not all(conflict.get("resolution_state") in {"reviewed", "accepted"} for conflict in conflicts):
                conflict_queue.append(
                    {
                        "canonical_id": canonical_id,
                        "comparison_key": group_key[0],
                        "comparison_value": group_key[1],
                        "conflicts": conflicts,
                    }
                )

        selected = sorted(
            records,
            key=lambda record: _precedence_index(str(record.get("source_id") or "")),
        )[0]
        supporting_sources = [
            _supporting_source(record, item["source_manifest_sha256"])
            for record, item in sorted(
                zip(records, items, strict=False),
                key=lambda pair: _precedence_index(str(pair[0].get("source_id") or "")),
            )
        ]
        canonical_record = {
            "canonical_id": canonical_id,
            "canonical_uri": _canonical_uri(canonical_id),
            "canonical_source": canonical_source,
            "supporting_sources": supporting_sources,
            "conflicts": conflicts,
            "confidence": confidence,
            "normalization_version": CANONICAL_BUILDER_VERSION,
            "title": _choose_value(records, fields=_TITLE_FIELDS) or None,
            "source_url": _source_url(selected) or None,
            "rights_note": _choose_value(records, fields=("rights_note",)) or (
                str(selected.get("rights_note") or "").strip()
            ),
            "coverage_state": coverage_state,
            "historical_only": historical_only,
            "provenance": {
                "pipeline_name": "nz-gazette-canonical-builder",
                "pipeline_version": CANONICAL_BUILDER_VERSION,
                "comparison_run_id": comparison_run_id,
                "source_manifest_sha256": sha256_text(
                    json.dumps(
                        {
                            "sources": [
                                {
                                    "source_id": item["record"]["source_id"],
                                    "source_manifest_sha256": item["source_manifest_sha256"],
                                }
                                for item in items
                            ],
                            "group_key": group_key,
                            "canonical_source": canonical_source,
                        },
                        sort_keys=True,
                        ensure_ascii=False,
                    )
                ),
                "release_version": CANONICAL_BUILDER_VERSION,
                "release_commit": CANONICAL_RELEASE_COMMIT,
                "license_note": (
                    "Canonical Gazette records are derived from independent source archives and "
                    "must not replace immutable raw source evidence."
                ),
            },
        }
        canonical_records.append({k: v for k, v in canonical_record.items() if v is not None})
        comparisons.append(
            {
                "canonical_id": canonical_id,
                "canonical_source": canonical_source,
                "group_key": group_key[0],
                "group_value": group_key[1],
                "source_ids": [str(record.get("source_id") or "") for record in records],
                "supporting_source_count": len(records),
                "exact_content_match": len({_source_content_hash(record) for record in records if _source_content_hash(record)}) <= 1,
                "confidence": confidence,
                "historical_only": historical_only,
                "conflict_count": len(conflicts),
            }
        )

    canonical_records.sort(key=lambda record: str(record["canonical_id"]))
    canonical_record_count = len(canonical_records)
    return {
        "canonical_records": canonical_records,
        "conflict_queue": conflict_queue,
        "comparison_report": {
            "schema_version": "1.0",
            "generated_at_utc": utc_now_iso(),
            "comparison_run_id": comparison_run_id,
            "canonical_record_count": canonical_record_count,
            "source_record_count": len(combined_records),
            "missing_source_count": len(missing_sources),
            "missing_sources": missing_sources,
            "matched_record_count": matched_count,
            "unmatched_record_count": unmatched_count,
            "conflicting_record_count": conflict_count,
            "historical_only_record_count": historical_only_count,
            "low_confidence_record_count": low_confidence_count,
            "exact_content_match_count": exact_match_count,
            "comparison_rows": comparisons,
        },
    }


def build_nz_gazette_canonical_review(
    *,
    canonical_records: Sequence[Mapping[str, Any]],
    conflict_queue: Sequence[Mapping[str, Any]],
    decisions: Sequence[Mapping[str, Any]] | None = None,
    missing_source_count: int = 0,
) -> dict[str, Any]:
    """Review canonical Gazette outputs and fail closed on unresolved conflicts."""
    missing_provenance = 0
    missing_rights = 0
    missing_supporting_sources = 0
    missing_canonical_id = 0
    unresolved_conflicts = 0
    conflict_decision_ids = set()
    for decision in decisions or []:
        canonical_id = str(decision.get("canonical_id") or "").strip()
        field_name = str(decision.get("field_name") or "").strip()
        if canonical_id and field_name:
            conflict_decision_ids.add((canonical_id, field_name))

    for record in canonical_records:
        if not str(record.get("canonical_id") or "").strip():
            missing_canonical_id += 1
        if not str(record.get("rights_note") or "").strip():
            missing_rights += 1
        if not isinstance(record.get("supporting_sources"), list) or not record["supporting_sources"]:
            missing_supporting_sources += 1
        provenance = record.get("provenance")
        if not isinstance(provenance, dict):
            missing_provenance += 1
        if record.get("conflicts"):
            for conflict in record["conflicts"]:
                key = (str(record.get("canonical_id") or ""), str(conflict.get("field_name") or ""))
                if conflict.get("resolution_state") not in {"reviewed", "accepted"} and key not in conflict_decision_ids:
                    unresolved_conflicts += 1

    ok = not any(
        [
            missing_provenance,
            missing_rights,
            missing_supporting_sources,
            missing_canonical_id,
            unresolved_conflicts,
        ]
    )
    coverage_warning = ""
    if not ok:
        coverage_warning = (
            "Canonical Gazette review failed. "
            f"provenance={missing_provenance}, rights={missing_rights}, "
            f"supporting_sources={missing_supporting_sources}, canonical_id={missing_canonical_id}, "
            f"unresolved_conflicts={unresolved_conflicts}."
        )
    return {
        "schema_version": "1.0",
        "ok": ok,
        "canonical_record_count": len(canonical_records),
        "conflict_queue_count": len(conflict_queue),
        "missing_source_count": missing_source_count,
        "missing_provenance_count": missing_provenance,
        "missing_rights_count": missing_rights,
        "missing_supporting_sources_count": missing_supporting_sources,
        "missing_canonical_id_count": missing_canonical_id,
        "unresolved_conflict_count": unresolved_conflicts,
        "coverage_warning": coverage_warning,
    }


def build_nz_gazette_canonical_coverage_report(
    *,
    canonical_records: Sequence[Mapping[str, Any]],
    comparison_report: Mapping[str, Any],
    review_report: Mapping[str, Any],
) -> dict[str, Any]:
    confidence_counts = Counter(str(record.get("confidence") or "unknown") for record in canonical_records)
    canonical_source_counts = Counter(
        str(record.get("canonical_source") or "") for record in canonical_records
    )
    coverage = {
        "schema_version": "1.0",
        "generated_at_utc": utc_now_iso(),
        "canonical_record_count": len(canonical_records),
        "comparison_record_count": int(comparison_report.get("source_record_count") or 0),
        "matched_record_count": int(comparison_report.get("matched_record_count") or 0),
        "unmatched_record_count": int(comparison_report.get("unmatched_record_count") or 0),
        "conflicting_record_count": int(comparison_report.get("conflicting_record_count") or 0),
        "historical_only_record_count": int(comparison_report.get("historical_only_record_count") or 0),
        "low_confidence_record_count": int(comparison_report.get("low_confidence_record_count") or 0),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "canonical_source_counts": dict(sorted(canonical_source_counts.items())),
        "review_ok": bool(review_report.get("ok")),
        "coverage_warning": str(review_report.get("coverage_warning") or ""),
    }
    coverage["content_sha256"] = sha256_text(
        json.dumps(coverage, sort_keys=True, ensure_ascii=False)
    )
    coverage["manifest_sha256"] = sha256_text(
        json.dumps({k: v for k, v in coverage.items() if k not in {"content_sha256", "manifest_sha256"}}, sort_keys=True, ensure_ascii=False)
    )
    return coverage


def write_nz_gazette_conflict_decisions_template(
    conflict_queue: Sequence[Mapping[str, Any]],
    output_path: Path,
) -> list[dict[str, Any]]:
    decisions = []
    for item in conflict_queue:
        canonical_id = str(item.get("canonical_id") or "")
        for conflict in item.get("conflicts") or []:
            field_name = str(conflict.get("field_name") or "")
            if not canonical_id or not field_name:
                continue
            decision = {
                "decision_id": f"{canonical_id}:{field_name}",
                "canonical_id": canonical_id,
                "field_name": field_name,
                "source_ids": list(conflict.get("source_ids") or []),
                "reviewer": "",
                "reviewed_at": "",
                "rationale": "",
                "selected_value": "",
                "evidence_links": [],
                "resolution_state": "reviewed",
            }
            decisions.append(decision)
    write_jsonl(output_path, decisions)
    return decisions


def export_nz_gazette_canonical_layer(
    *,
    official_source_dir: Path | None = None,
    digitalnz_source_dir: Path | None = None,
    historical_source_dir: Path | None = None,
    nzlii_source_dir: Path | None = None,
    output_dir: Path,
    year: str,
    comparison_run_id: str = DEFAULT_COMPARISON_RUN_ID,
    decisions_path: Path | None = None,
) -> dict[str, Any]:
    source_dirs: list[dict[str, Any]] = []
    for source_dir in (
        official_source_dir,
        digitalnz_source_dir,
        historical_source_dir,
        nzlii_source_dir,
    ):
        if source_dir is not None:
            source_dirs.append({"source_dir": source_dir})
    if not source_dirs:
        raise RuntimeError("At least one source archive directory is required")

    decision_records = read_jsonl(decisions_path) if decisions_path and decisions_path.exists() else []
    comparison = build_nz_gazette_canonical_records(
        source_dirs,
        decisions=decision_records,
        comparison_run_id=comparison_run_id,
    )
    canonical_records = comparison["canonical_records"]
    conflict_queue = comparison["conflict_queue"]
    comparison_report = comparison["comparison_report"]
    review_report = build_nz_gazette_canonical_review(
        canonical_records=canonical_records,
        conflict_queue=conflict_queue,
        decisions=decision_records,
        missing_source_count=int(comparison_report.get("missing_source_count") or 0),
    )
    coverage_report = build_nz_gazette_canonical_coverage_report(
        canonical_records=canonical_records,
        comparison_report=comparison_report,
        review_report=review_report,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "records.jsonl"
    canonical_records_path = output_dir / "canonical_records.jsonl"
    queue_path = output_dir / "conflict_queue.jsonl"
    decisions_out_path = output_dir / "gazette_conflict_decisions.jsonl"
    comparison_path = output_dir / "manifests" / "comparison_report.json"
    review_path = output_dir / "manifests" / "review_report.json"
    coverage_path = output_dir / "manifests" / "coverage_report.json"
    state_path = output_dir / "_state" / "comparison_state.json"
    output_dir.joinpath("manifests").mkdir(parents=True, exist_ok=True)
    output_dir.joinpath("_state").mkdir(parents=True, exist_ok=True)

    write_jsonl(records_path, canonical_records)
    write_jsonl(canonical_records_path, canonical_records)
    write_jsonl(queue_path, conflict_queue)
    if decision_records:
        write_jsonl(decisions_out_path, decision_records)
    else:
        decisions_out_path.write_text("", encoding="utf-8")
    write_json(comparison_path, comparison_report)
    write_json(review_path, review_report)
    write_json(coverage_path, coverage_report)
    write_json(
        state_path,
        {
            "schema_version": "1.0",
            "comparison_run_id": comparison_run_id,
            "record_count": len(canonical_records),
            "conflict_queue_count": len(conflict_queue),
            "review_ok": review_report["ok"],
            "coverage_warning": review_report["coverage_warning"],
        },
    )

    archive_output_dir = _archive_output_dir(output_dir)
    bundle = build_archive(
        output_dir,
        archive_output_dir,
        year=year,
        archive_name_prefix=CANONICAL_ARCHIVE_PREFIX,
        manifest_name_prefix=CANONICAL_ARCHIVE_PREFIX,
        tar_root_name=CANONICAL_ARCHIVE_PREFIX,
        artifact_class="nz_gazette_canonical_archive",
        publication_target="source_evidence",
        coverage_statement=(
            "Canonical Gazette records are derived from independent source archives and "
            "must not replace immutable raw source evidence."
        ),
    )

    manifest_path = Path(bundle["manifest_path"])
    release_path = Path(bundle["provenance_path"])
    build_release_evidence(
        artifact_class="nz_gazette_canonical_archive",
        output_path=release_path,
        subjects=[Path(bundle["archive_path"]), manifest_path, comparison_path, review_path],
        manifest=read_json(manifest_path, default={}) or {},
        coverage_statement=(
            "Canonical Gazette records are derived from independent source archives and "
            "must not replace immutable raw source evidence."
        ),
        publication_target="source_evidence",
    )
    checksums_path = output_dir / f"{CANONICAL_ARCHIVE_PREFIX}-{year}.SHA256SUMS.txt"
    lines = [
        f"{sha256_file(Path(bundle['archive_path']))}  {Path(bundle['archive_path']).name}",
        f"{sha256_file(manifest_path)}  {manifest_path.name}",
        f"{sha256_file(release_path)}  {release_path.name}",
        f"{sha256_file(comparison_path)}  {comparison_path.name}",
        f"{sha256_file(review_path)}  {review_path.name}",
        f"{sha256_file(coverage_path)}  {coverage_path.name}",
    ]
    checksums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "ok": review_report["ok"],
        "comparison_run_id": comparison_run_id,
        "canonical_record_count": len(canonical_records),
        "comparison_report_path": str(comparison_path),
        "review_report_path": str(review_path),
        "coverage_path": str(coverage_path),
        "records_path": str(records_path),
        "canonical_records_path": str(canonical_records_path),
        "conflict_queue_path": str(queue_path),
        "conflict_decisions_path": str(decisions_out_path),
        "state_path": str(state_path),
        "archive_path": bundle["archive_path"],
        "manifest_path": str(manifest_path),
        "release_evidence_path": str(release_path),
        "checksums_path": str(checksums_path),
        "comparison_report": comparison_report,
        "review_report": review_report,
        "coverage_report": coverage_report,
        "canonical_records": canonical_records,
        "conflict_queue": conflict_queue,
    }


def build_nz_gazette_canonical_archive(
    source_trees: Sequence[Mapping[str, Any]],
    output_dir: Path,
    *,
    year: str,
    comparison_run_id: str = DEFAULT_COMPARISON_RUN_ID,
    decisions_path: Path | None = None,
) -> dict[str, Any]:
    """Backwards-compatible wrapper for the canonical archive builder."""
    source_map = {
        str(source_tree.get("source_id") or ""): Path(source_tree["source_dir"])
        for source_tree in source_trees
        if str(source_tree.get("source_id") or "").strip()
    }
    return export_nz_gazette_canonical_layer(
        official_source_dir=source_map.get("official_gazette"),
        digitalnz_source_dir=source_map.get("digitalnz_gazette"),
        historical_source_dir=source_map.get("victoria_lexisnexis_gazette"),
        nzlii_source_dir=source_map.get("nzlii_gazette"),
        output_dir=Path(output_dir),
        year=year,
        comparison_run_id=comparison_run_id,
        decisions_path=decisions_path,
    )
