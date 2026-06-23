from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .discovery import normalize_work_ids, sha256_lines
from .utils import read_json, write_json

YEAR_RE = re.compile(r"(?<!\d)(1[5-9]\d{2}|20\d{2})(?!\d)")
UNKNOWN_PERIOD = "unknown_year_review"
UNVERIFIED_BOUNDARY_WARNING = (
    "Annual recent shards start at the conservative planning fallback. "
    "Do not treat the API-native/recent boundary as verified until "
    "api_boundary_verified is true and api_boundary_source names the evidence."
)


def _year_from_text(value: Any) -> int | None:
    if value is None:
        return None
    match = YEAR_RE.search(str(value))
    return int(match.group(1)) if match else None


def derive_work_year(work_id: str, metadata: dict[str, Any] | None = None) -> tuple[int | None, str]:
    """Derive a work year from source metadata fields."""
    metadata = metadata or {}
    for field in ("work_id", "latest_version_id", "title"):
        value = work_id if field == "work_id" else metadata.get(field)
        year = _year_from_text(value)
        if year is not None:
            return year, field
    return None, "unknown"


def assign_period(year: int | None, *, api_boundary_year: int) -> str:
    """Assign a derived year to the canonical period policy."""
    if year is None:
        return UNKNOWN_PERIOD
    historical_periods = (
        (1907, "pre_1908"),
        (1949, "1908_1949"),
        (1979, "1950_1979"),
        (1999, "1980_1999"),
    )
    for upper_bound, period_id in historical_periods:
        if year <= upper_bound:
            return period_id
    if year < api_boundary_year:
        return f"2000_{api_boundary_year - 1}"
    return f"year_{year}"


def build_api_boundary_decision(
    *,
    api_boundary_year: int,
    api_boundary_source: str,
    api_boundary_verified: bool,
) -> dict[str, Any]:
    """Build the manifest evidence for the annual recent-shard boundary."""
    return {
        "boundary_year": api_boundary_year,
        "source": api_boundary_source,
        "verified": api_boundary_verified,
        "status": "verified" if api_boundary_verified else "planning_fallback_unverified",
        "annual_shards_start_year": api_boundary_year,
        "warning": None if api_boundary_verified else UNVERIFIED_BOUNDARY_WARNING,
    }


def _load_source_metadata(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    payload = read_json(path, default={}) or {}
    works = payload.get("works") if isinstance(payload, dict) else None
    if not isinstance(works, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for work in works:
        if not isinstance(work, dict):
            continue
        work_id = str(work.get("work_id") or "").strip()
        if work_id:
            result[work_id] = work
    return result


def build_period_manifest(
    work_ids: list[str],
    *,
    source_metadata: dict[str, dict[str, Any]] | None = None,
    api_boundary_year: int = 2008,
    api_boundary_source: str = "planning_fallback_unverified",
    api_boundary_verified: bool = False,
    filename_suffix: str = ".txt",
) -> dict[str, Any]:
    """Build a period-shard manifest without making completeness claims."""
    normalized = normalize_work_ids(work_ids)
    metadata = source_metadata or {}
    period_work_ids: dict[str, list[str]] = defaultdict(list)
    assignments: list[dict[str, Any]] = []
    seen_assignments: set[str] = set()
    duplicate_assignments: list[str] = []

    for work_id in normalized:
        year, year_source = derive_work_year(work_id, metadata.get(work_id))
        period_id = assign_period(year, api_boundary_year=api_boundary_year)
        if work_id in seen_assignments:
            duplicate_assignments.append(work_id)
        seen_assignments.add(work_id)
        period_work_ids[period_id].append(work_id)
        assignments.append(
            {
                "work_id": work_id,
                "year": year,
                "year_source": year_source,
                "period_id": period_id,
            }
        )

    periods = []
    for period_id, period_ids in sorted(period_work_ids.items()):
        periods.append(
            {
                "period_id": period_id,
                "filename": f"{period_id}{filename_suffix}",
                "work_id_count": len(period_ids),
                "first_work_id": period_ids[0] if period_ids else None,
                "last_work_id": period_ids[-1] if period_ids else None,
                "sha256": sha256_lines(period_ids),
                "status": "ready_for_generation",
            }
        )

    assigned = {assignment["work_id"] for assignment in assignments}
    unassigned = sorted(set(normalized) - assigned)
    return {
        "schema_version": "1.0",
        "source_record_count": len([work_id for work_id in work_ids if work_id.strip()]),
        "unique_work_id_count": len(normalized),
        "assigned_work_id_count": len(assignments),
        "period_count": len(periods),
        "seed_sha256": sha256_lines(normalized),
        "api_boundary_year": api_boundary_year,
        "api_boundary_source": api_boundary_source,
        "api_boundary_verified": api_boundary_verified,
        "api_boundary_decision": build_api_boundary_decision(
            api_boundary_year=api_boundary_year,
            api_boundary_source=api_boundary_source,
            api_boundary_verified=api_boundary_verified,
        ),
        "year_derivation_fields": ["work_id", "latest_version_id", "title"],
        "period_policy": {
            "historical": ["pre_1908", "1908_1949", "1950_1979", "1980_1999"],
            "pre_api_boundary": f"2000_{api_boundary_year - 1}",
            "recent": f"annual from {api_boundary_year}",
            "unknown": UNKNOWN_PERIOD,
        },
        "periods": periods,
        "assignments": assignments,
        "unassigned_work_ids": unassigned,
        "duplicate_assignments": sorted(duplicate_assignments),
        "coverage_warning": (
            "Period shards are only as complete as the reviewed source inventory. "
            "Do not claim full coverage until all periods are reviewed and reconciled."
        ),
    }


def split_period_seed_files(
    seed_work_ids_path: Path,
    *,
    output_dir: Path,
    manifest_path: Path,
    source_metadata_path: Path | None = None,
    api_boundary_year: int = 2008,
    api_boundary_source: str = "planning_fallback_unverified",
    api_boundary_verified: bool = False,
) -> dict[str, Any]:
    """Write period seed files and a period manifest."""
    lines = seed_work_ids_path.read_text(encoding="utf-8").splitlines()
    source_metadata = _load_source_metadata(source_metadata_path)
    manifest = build_period_manifest(
        lines,
        source_metadata=source_metadata,
        api_boundary_year=api_boundary_year,
        api_boundary_source=api_boundary_source,
        api_boundary_verified=api_boundary_verified,
    )
    period_map: dict[str, list[str]] = defaultdict(list)
    for assignment in manifest["assignments"]:
        period_map[str(assignment["period_id"])].append(str(assignment["work_id"]))

    output_dir.mkdir(parents=True, exist_ok=True)
    for period in manifest["periods"]:
        period_id = str(period["period_id"])
        path = output_dir / str(period["filename"])
        ids = period_map[period_id]
        path.write_text("\n".join(ids) + ("\n" if ids else ""), encoding="utf-8")

    write_json(manifest_path, manifest)
    return manifest
