from __future__ import annotations

from typing import Any

from nz_legislation_corpus.cli import _optional_filter
from nz_legislation_corpus.discovery import (
    build_work_id_batch_manifest,
    build_work_id_inventory,
    normalize_work_ids,
    sha256_lines,
)


class FakeDiscoveryClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def iter_search_works(self, **kwargs: Any):
        self.calls.append(kwargs)
        yield {
            "work_id": "work-2",
            "title": "Second",
            "legislation_type": kwargs.get("legislation_type"),
            "legislation_status": kwargs.get("legislation_status"),
            "latest_matching_version": {"version_id": "work-2-v1"},
        }
        yield {
            "work_id": "work-1",
            "title": "First",
            "legislation_type": kwargs.get("legislation_type"),
            "legislation_status": kwargs.get("legislation_status"),
            "latest_matching_version": {"version_id": "work-1-v1"},
        }
        yield {"work_id": "work-2", "title": "Duplicate"}


def test_build_work_id_inventory_deduplicates_and_records_provenance() -> None:
    client = FakeDiscoveryClient()

    inventory = build_work_id_inventory(
        client,
        search_terms=["act"],
        search_field="title",
        legislation_types=["act"],
        legislation_status="historical",
        sort_by="most_recently_updated",
        publisher=None,
        max_pages=2,
        max_works=None,
    )

    assert inventory["work_ids"] == ["work-1", "work-2"]
    assert inventory["record_count"] == 2
    assert inventory["works"][0]["work_id"] == "work-1"
    assert inventory["queries"] == [
        {
            "search_term": "act",
            "search_field": "title",
            "legislation_type": "act",
            "legislation_status": "historical",
            "works_added": 2,
            "max_pages": 2,
        }
    ]
    assert client.calls[0]["legislation_status"] == "historical"


def test_build_work_id_inventory_honors_max_works() -> None:
    inventory = build_work_id_inventory(
        FakeDiscoveryClient(),
        search_terms=["act", "bill"],
        search_field="title",
        legislation_types=["act"],
        legislation_status="historical",
        sort_by=None,
        publisher=None,
        max_pages=None,
        max_works=1,
    )

    assert inventory["work_ids"] == ["work-2"]
    assert inventory["record_count"] == 1


def test_optional_filter_omits_blank_and_none_sentinels() -> None:
    assert _optional_filter(None, "current") == "current"
    assert _optional_filter(" historical ", None) == "historical"
    assert _optional_filter("", "current") is None
    assert _optional_filter("none", "current") is None
    assert _optional_filter("NULL", "current") is None
    assert _optional_filter("-", "current") is None


def test_normalize_work_ids_sorts_deduplicates_and_ignores_comments() -> None:
    assert normalize_work_ids(
        [
            "work-2",
            "",
            "# comment",
            " work-1 ",
            "work-2",
            "   # indented comment",
        ]
    ) == ["work-1", "work-2"]


def test_build_work_id_batch_manifest_is_stable() -> None:
    manifest = build_work_id_batch_manifest(
        ["work-3", "work-1", "work-2", "work-2"],
        batch_size=2,
        filename_prefix="batch",
    )

    assert manifest["unique_record_count"] == 3
    assert manifest["batch_count"] == 2
    assert manifest["seed_sha256"] == sha256_lines(["work-1", "work-2", "work-3"])
    assert manifest["batches"] == [
        {
            "index": 1,
            "filename": "batch-0001.txt",
            "record_count": 2,
            "first_work_id": "work-1",
            "last_work_id": "work-2",
            "sha256": sha256_lines(["work-1", "work-2"]),
        },
        {
            "index": 2,
            "filename": "batch-0002.txt",
            "record_count": 1,
            "first_work_id": "work-3",
            "last_work_id": "work-3",
            "sha256": sha256_lines(["work-3"]),
        },
    ]
