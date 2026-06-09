from __future__ import annotations

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
