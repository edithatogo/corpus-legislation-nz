from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any, Protocol


class WorkSearchClient(Protocol):
    def iter_search_works(
        self,
        *,
        search_term: str,
        search_field: str = "title",
        per_page: int | None = None,
        max_pages: int | None = None,
        legislation_type: str | None = None,
        legislation_status: str | None = None,
        sort_by: str | None = None,
        publisher: str | None = None,
    ) -> Iterator[dict[str, Any]]: ...


def build_work_id_inventory(
    client: WorkSearchClient,
    *,
    search_terms: list[str],
    search_field: str,
    legislation_types: list[str],
    legislation_status: str | None,
    sort_by: str | None,
    publisher: str | None,
    max_pages: int | None,
    max_works: int | None,
) -> dict[str, Any]:
    """Discover unique work IDs from search-oriented API results."""
    type_filters: list[str | None] = list(legislation_types) if legislation_types else [None]
    seen_work_ids: set[str] = set()
    works: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []

    for term in search_terms:
        for leg_type in type_filters:
            query_count = 0
            for work in client.iter_search_works(
                search_term=term,
                search_field=search_field,
                max_pages=max_pages,
                legislation_type=leg_type,
                legislation_status=legislation_status,
                sort_by=sort_by,
                publisher=publisher,
            ):
                work_id = str(work.get("work_id") or "").strip()
                if not work_id or work_id in seen_work_ids:
                    continue
                seen_work_ids.add(work_id)
                query_count += 1
                works.append(
                    {
                        "work_id": work_id,
                        "title": work.get("title"),
                        "legislation_type": work.get("legislation_type"),
                        "legislation_status": work.get("legislation_status"),
                        "latest_version_id": (work.get("latest_matching_version") or {}).get(
                            "version_id"
                        )
                        if isinstance(work.get("latest_matching_version"), dict)
                        else None,
                    }
                )
                if max_works is not None and len(works) >= max_works:
                    break
            queries.append(
                {
                    "search_term": term,
                    "search_field": search_field,
                    "legislation_type": leg_type,
                    "legislation_status": legislation_status,
                    "works_added": query_count,
                    "max_pages": max_pages,
                }
            )
            if max_works is not None and len(works) >= max_works:
                break
        if max_works is not None and len(works) >= max_works:
            break

    works.sort(key=lambda item: str(item["work_id"]))
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "record_count": len(works),
        "work_ids": [str(work["work_id"]) for work in works],
        "works": works,
        "queries": queries,
        "coverage_warning": (
            "This is a search-derived inventory, not proof of full corpus coverage. "
            "Reconcile against an authoritative inventory before claiming completeness."
        ),
    }


def normalize_work_ids(lines: list[str]) -> list[str]:
    """Return stable, de-duplicated work IDs from a line-oriented seed file."""
    work_ids = {
        line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")
    }
    return sorted(work_ids)


def sha256_lines(lines: list[str]) -> str:
    payload = "".join(f"{line}\n" for line in lines)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_work_id_batch_manifest(
    work_ids: list[str],
    *,
    batch_size: int,
    filename_prefix: str = "historical-work-ids",
) -> dict[str, Any]:
    """Describe deterministic seed batches without making coverage claims."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    normalized = normalize_work_ids(work_ids)
    batches: list[dict[str, Any]] = []
    for offset in range(0, len(normalized), batch_size):
        batch = normalized[offset : offset + batch_size]
        index = len(batches) + 1
        filename = f"{filename_prefix}-{index:04d}.txt"
        batches.append(
            {
                "index": index,
                "filename": filename,
                "record_count": len(batch),
                "first_work_id": batch[0] if batch else None,
                "last_work_id": batch[-1] if batch else None,
                "sha256": sha256_lines(batch),
            }
        )
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_record_count": len([line for line in work_ids if line.strip()]),
        "unique_record_count": len(normalized),
        "batch_size": batch_size,
        "batch_count": len(batches),
        "seed_sha256": sha256_lines(normalized),
        "batches": batches,
        "coverage_warning": (
            "Seed batches are only as complete as the reviewed source inventory. "
            "Do not claim full historical coverage until the source inventory is reconciled."
        ),
    }


def build_work_id_reconciliation_report(
    *,
    baseline_lines: list[str],
    candidate_lines: list[str],
    baseline_label: str = "baseline",
    candidate_label: str = "candidate",
) -> dict[str, Any]:
    """Compare two work-ID inventories without making completeness claims."""
    baseline = normalize_work_ids(baseline_lines)
    candidate = normalize_work_ids(candidate_lines)
    baseline_set = set(baseline)
    candidate_set = set(candidate)
    added = sorted(candidate_set - baseline_set)
    removed = sorted(baseline_set - candidate_set)
    unchanged = sorted(baseline_set & candidate_set)
    merged = sorted(baseline_set | candidate_set)
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "baseline_label": baseline_label,
        "candidate_label": candidate_label,
        "baseline_unique_count": len(baseline),
        "candidate_unique_count": len(candidate),
        "unchanged_count": len(unchanged),
        "added_count": len(added),
        "removed_count": len(removed),
        "merged_unique_count": len(merged),
        "baseline_sha256": sha256_lines(baseline),
        "candidate_sha256": sha256_lines(candidate),
        "merged_sha256": sha256_lines(merged),
        "added_work_ids": added,
        "removed_work_ids": removed,
        "coverage_warning": (
            "This reconciliation compares two work-ID inventories only. "
            "It is not proof of complete corpus coverage unless one input is an "
            "authoritative complete inventory or has been externally reconciled."
        ),
    }
