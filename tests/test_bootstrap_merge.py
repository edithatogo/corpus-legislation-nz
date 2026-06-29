from __future__ import annotations

import json
from pathlib import Path

import pytest

from nz_legislation_corpus.bootstrap_merge import merge_bootstrap_artifacts
from nz_legislation_corpus.bootstrap_review import build_full_corpus_bootstrap_review
from nz_legislation_corpus.utils import sha256_text, write_json, write_jsonl


def _record(stable_id: str, *, title: str) -> dict[str, object]:
    source_hash = sha256_text(stable_id)
    text_hash = sha256_text(title)
    return {
        "record_schema_version": "1.0",
        "stable_id": stable_id,
        "work_id": stable_id,
        "version_id": f"{stable_id}/latest",
        "title": title,
        "jurisdiction": "New Zealand",
        "country": "NZ",
        "source": "NZ Legislation",
        "source_url": f"https://example.invalid/{stable_id}",
        "api_url": f"https://example.invalid/api/{stable_id}",
        "legislation_type": "act",
        "legislation_status": "in_force",
        "administering_agencies": [],
        "version_date": "2026-01-01",
        "year": 2026,
        "is_latest_version": True,
        "xml_url": f"https://example.invalid/{stable_id}.xml",
        "text": title,
        "text_sha256": text_hash,
        "source_hash": source_hash,
        "scrape_date": "2026-01-01",
        "ingest_timestamp_utc": "2026-01-01T00:00:00+00:00",
        "language": "en",
        "pipeline_version": "test",
    }


def _write_artifact(root: Path, records: list[dict[str, object]]) -> None:
    data = root / "data"
    write_jsonl(data / "records.jsonl", records)
    write_json(
        data / "_state" / "sync_state.json",
        {
            "versions": {str(r["stable_id"]): str(r["source_hash"]) for r in records},
            "last_stats": {
                "works_checked": len(records),
                "versions_checked": len(records),
                "records_added": len(records),
                "records_changed": 0,
                "records_unchanged": 0,
                "records_failed": 0,
                "warnings": [],
                "parquet_files_written": 1,
            },
        },
    )
    raw_dir = data / "raw_xml"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        (raw_dir / f"{record['stable_id']}.xml").write_text("<act />", encoding="utf-8")


@pytest.mark.unit
def test_merge_bootstrap_artifacts_dedupes_and_reviews(tmp_path: Path) -> None:
    artifact_a = tmp_path / "artifact-a"
    artifact_b = tmp_path / "artifact-b"
    output = tmp_path / "merged"
    _write_artifact(artifact_a, [_record("act_public_2026_1", title="One")])
    _write_artifact(
        artifact_b,
        [
            _record("act_public_2026_1", title="One updated"),
            _record("act_public_2026_2", title="Two"),
        ],
    )

    report = merge_bootstrap_artifacts([artifact_a, artifact_b], output)

    assert report["artifact_count"] == 2
    assert report["record_count"] == 2
    assert report["validation_ok"] is True
    records = [
        json.loads(line)
        for line in (output / "records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [r["stable_id"] for r in records] == ["act_public_2026_1", "act_public_2026_2"]
    assert records[0]["title"] == "One updated"
    assert (output / "manifests" / "latest_manifest.json").exists()
    assert (output / "manifests" / "coverage_report.json").exists()
    assert (output / "_state" / "sync_state.json").exists()
    assert build_full_corpus_bootstrap_review(output)["ok"] is True


@pytest.mark.unit
def test_merge_bootstrap_artifacts_rejects_empty_artifact(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No records found"):
        merge_bootstrap_artifacts([tmp_path / "empty"], tmp_path / "merged")
