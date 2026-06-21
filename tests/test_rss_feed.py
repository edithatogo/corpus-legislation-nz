from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import pytest

from nz_legislation_corpus.rss_feed import FEED_FILENAME, build_feed


def _make_records_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return path


def _make_changes_json(path: Path, added: list[str], changed: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "added": added,
        "changed": changed,
        "removed": [],
        "generated_at_utc": "2026-06-12T11:03:09+00:00",
        "has_changes": bool(added or changed),
        "current_manifest_sha256": "abc123",
        "previous_manifest_sha256": "def456",
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.mark.unit
def test_build_feed_creates_valid_rss(tmp_path: Path) -> None:
    records = [
        {
            "stable_id": "act_public_2026_26",
            "title": "Test Act 2026",
            "legislation_type": "act",
            "year": "2026",
            "legislation_status": "current",
            "html_url": "https://www.legislation.govt.nz/act/public/2026/26/en/latest",
            "xml_url": "https://www.legislation.govt.nz/act/public/2026/26/en/latest.xml",
        },
        {
            "stable_id": "bill_government_2025_100",
            "title": "Sample Bill 2025",
            "legislation_type": "bill",
            "year": "2025",
            "legislation_status": "before_parliament",
            "html_url": "",
            "xml_url": "",
        },
    ]
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", records)
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=["act_public_2026_26"],
        changed=["bill_government_2025_100"],
    )
    output_path = tmp_path / FEED_FILENAME

    result = build_feed(records_path, changes_path, output_path)

    assert result["ok"] is True
    assert result["item_count"] == 2
    assert output_path.exists()

    tree = ET.parse(output_path)
    root = tree.getroot()
    assert root.tag == "rss"
    assert root.attrib["version"] == "2.0"

    channel = root.find("channel")
    assert channel is not None
    assert channel.findtext("title") == "New Zealand Legislation Corpus - Recent Changes"

    items = channel.findall("item")
    assert len(items) == 2

    first = items[0]
    assert first.findtext("title") == "Test Act 2026 - 2026 (Act)"
    assert "Added to corpus" in (first.findtext("description") or "")
    assert first.findtext("category") == "Act"
    assert first.findtext("guid") == "act_public_2026_26"


@pytest.mark.unit
def test_build_feed_empty_changes(tmp_path: Path) -> None:
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", [])
    changes_path = _make_changes_json(tmp_path / "latest_changes.json", [], [])
    output_path = tmp_path / FEED_FILENAME

    result = build_feed(records_path, changes_path, output_path)

    assert result["ok"] is True
    assert result["item_count"] == 0
    tree = ET.parse(output_path)
    assert len(tree.getroot().findall(".//item")) == 0


@pytest.mark.unit
def test_build_feed_respects_max_items(tmp_path: Path) -> None:
    records = [
        {"stable_id": f"act_public_2026_{i}", "title": f"Act {i}", "legislation_type": "act"}
        for i in range(10)
    ]
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", records)
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=[f"act_public_2026_{i}" for i in range(10)],
        changed=[],
    )
    output_path = tmp_path / FEED_FILENAME

    result = build_feed(records_path, changes_path, output_path, max_items=3)

    assert result["item_count"] == 3
    tree = ET.parse(output_path)
    assert len(tree.getroot().findall(".//item")) == 3


@pytest.mark.unit
def test_build_feed_uses_fallback_url(tmp_path: Path) -> None:
    records = [
        {
            "stable_id": "act_public_1900_1",
            "title": "Old Act",
            "legislation_type": "act",
            "html_url": "",
            "xml_url": "",
        },
    ]
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", records)
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=["act_public_1900_1"],
        changed=[],
    )
    output_path = tmp_path / FEED_FILENAME

    build_feed(records_path, changes_path, output_path)

    tree = ET.parse(output_path)
    link = tree.getroot().findtext(".//item/link")
    assert link == "https://huggingface.co/datasets/edithatogo/corpus-legislation-nz"


@pytest.mark.unit
def test_build_feed_missing_changes_file(tmp_path: Path) -> None:
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", [])
    changes_path = tmp_path / "nonexistent_changes.json"
    output_path = tmp_path / FEED_FILENAME

    result = build_feed(records_path, changes_path, output_path)

    assert result["ok"] is True
    assert result["item_count"] == 0
    tree = ET.parse(output_path)
    assert len(tree.getroot().findall(".//item")) == 0


@pytest.mark.unit
def test_build_feed_missing_records_file(tmp_path: Path) -> None:
    """When records file is missing but changes reference IDs, items are created with sid as title."""
    records_path = tmp_path / "nonexistent_records.jsonl"
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=["act_public_2026_26"],
        changed=[],
    )
    output_path = tmp_path / FEED_FILENAME

    result = build_feed(records_path, changes_path, output_path)

    assert result["ok"] is True
    # Items are still created from changes IDs, using sid as fallback title
    assert result["item_count"] == 1
    tree = ET.parse(output_path)
    item = tree.getroot().findall(".//item")[0]
    assert item.findtext("title") == "act_public_2026_26 ()"


@pytest.mark.unit
def test_build_feed_deduplicates_ids(tmp_path: Path) -> None:
    """When an ID appears in both added and changed lists, it should appear once."""
    records = [
        {
            "stable_id": "act_public_2026_26",
            "title": "Test Act 2026",
            "legislation_type": "act",
            "year": "2026",
            "legislation_status": "current",
        },
    ]
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", records)
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=["act_public_2026_26"],
        changed=["act_public_2026_26"],
    )
    output_path = tmp_path / FEED_FILENAME

    result = build_feed(records_path, changes_path, output_path)

    assert result["item_count"] == 1
    tree = ET.parse(output_path)
    items = tree.getroot().findall(".//item")
    assert len(items) == 1
    desc = items[0].findtext("description") or ""
    assert "Added to corpus" in desc
    assert "Updated" in desc


@pytest.mark.unit
def test_build_feed_secondary_legislation_label(tmp_path: Path) -> None:
    records = [
        {
            "stable_id": "sec_leg_2024_001",
            "title": "Reg 2024",
            "legislation_type": "secondary_legislation",
            "year": "2024",
        },
    ]
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", records)
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=["sec_leg_2024_001"],
        changed=[],
    )
    output_path = tmp_path / FEED_FILENAME

    result = build_feed(records_path, changes_path, output_path)

    assert result["item_count"] == 1
    tree = ET.parse(output_path)
    item = tree.getroot().findall(".//item")[0]
    assert item.findtext("category") == "Secondary Legislation"
    assert "Secondary Legislation" in (item.findtext("title") or "")


@pytest.mark.unit
def test_build_feed_amendment_paper_label(tmp_path: Path) -> None:
    records = [
        {
            "stable_id": "amp_paper_2025_001",
            "title": "Amendment Paper 2025",
            "legislation_type": "amendment_paper",
            "year": "2025",
        },
    ]
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", records)
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=["amp_paper_2025_001"],
        changed=[],
    )
    output_path = tmp_path / FEED_FILENAME

    build_feed(records_path, changes_path, output_path)

    tree = ET.parse(output_path)
    item = tree.getroot().findall(".//item")[0]
    assert item.findtext("category") == "Amendment Paper"


@pytest.mark.unit
def test_build_feed_unknown_type_label(tmp_path: Path) -> None:
    records = [
        {
            "stable_id": "unknown_type_001",
            "title": "Mystery Document",
            "legislation_type": "unknown_format",
        },
    ]
    records_path = _make_records_jsonl(tmp_path / "records.jsonl", records)
    changes_path = _make_changes_json(
        tmp_path / "latest_changes.json",
        added=["unknown_type_001"],
        changed=[],
    )
    output_path = tmp_path / FEED_FILENAME

    build_feed(records_path, changes_path, output_path)

    tree = ET.parse(output_path)
    item = tree.getroot().findall(".//item")[0]
    assert "Unknown Format" in (item.findtext("title") or "")
    assert item.findtext("category") == "Unknown Format"
