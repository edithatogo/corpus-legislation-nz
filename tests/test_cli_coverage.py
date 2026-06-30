from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nz_legislation_corpus.cli import coverage_report_cmd
from nz_legislation_corpus.utils import write_jsonl


def _make_records(records: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "records.jsonl", records)


@pytest.mark.unit
def test_coverage_report_empty(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "data"
    _make_records([], output_dir)
    manifests_dir = output_dir / "manifests"
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))

    coverage_report_cmd()

    report = json.loads((manifests_dir / "coverage_report.json").read_text(encoding="utf-8"))
    assert report["record_count"] == 0
    assert report["by_type"] == {}
    assert report["by_status"] == {}
    assert report["by_year"] == {}
    risk = report["risk_indicators"]
    assert risk["missing_text_records"] == 0
    assert risk["missing_xml_url_records"] == 0
    assert risk["ephemeral_identifier_records"] == 0
    assert "No records found" in report["recommendation"]

    assert (manifests_dir / "coverage_history.jsonl").exists()


@pytest.mark.unit
def test_coverage_report_with_records(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "data"
    records = [
        {
            "stable_id": "act_public_2026_26",
            "title": "Test Act 2026",
            "legislation_type": "act",
            "legislation_status": "current",
            "year": 2026,
            "text": "Some legislative text here",
            "xml_url": "https://example.invalid/act.xml",
        },
        {
            "stable_id": "bill_government_2025_100",
            "title": "Sample Bill 2025",
            "legislation_type": "bill",
            "legislation_status": "before_parliament",
            "year": 2025,
            "text": "Bill text content",
            "xml_url": "",
        },
        {
            "stable_id": "sec_leg_2024_001",
            "title": "Reg 2024",
            "legislation_type": "secondary_legislation",
            "legislation_status": "current",
            "year": 2024,
            "text": "",
            "xml_url": "",
            "id_is_ephemeral": True,
        },
    ]
    _make_records(records, output_dir)
    manifests_dir = output_dir / "manifests"
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))

    coverage_report_cmd()

    report = json.loads((manifests_dir / "coverage_report.json").read_text(encoding="utf-8"))
    assert report["record_count"] == 3
    assert report["by_type"] == {
        "act": 1,
        "bill": 1,
        "secondary_legislation": 1,
    }
    assert report["by_status"] == {
        "before_parliament": 1,
        "current": 2,
    }
    assert report["by_year"] == {
        "2024": 1,
        "2025": 1,
        "2026": 1,
    }
    risk = report["risk_indicators"]
    assert risk["missing_text_records"] == 1  # sec_leg_2024_001 has empty text
    assert risk["missing_xml_url_records"] == 2  # bill and sec_leg have no xml_url
    assert risk["ephemeral_identifier_records"] == 1
    assert "Review merged shard provenance" in report["recommendation"]


@pytest.mark.unit
def test_coverage_report_appends_history(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "data"
    records = [
        {
            "stable_id": "act_public_2026_26",
            "title": "Test Act 2026",
            "legislation_type": "act",
            "legislation_status": "current",
            "year": 2026,
            "text": "text",
            "xml_url": "https://example.invalid/act.xml",
        },
    ]
    _make_records(records, output_dir)
    manifests_dir = output_dir / "manifests"
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))

    coverage_report_cmd()
    coverage_report_cmd()

    history_lines = (
        (manifests_dir / "coverage_history.jsonl").read_text(encoding="utf-8").strip().splitlines()
    )
    assert len(history_lines) == 2
