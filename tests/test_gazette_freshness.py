from __future__ import annotations

import json
from pathlib import Path

from nz_legislation_corpus.gazette_freshness import (
    CANONICAL_TRACK_ID,
    DIGITALNZ_GAZETTE_SOURCE_ID,
    OFFICIAL_GAZETTE_SOURCE_ID,
    FreshnessObservation,
    _combine_observations,
    build_gazette_freshness_report,
)


def _observation(
    source_id: str,
    item_id: str,
    *,
    content_hash: str,
    retrieved_at_utc: str = "2026-07-03T00:00:00Z",
    source_url: str = "https://example.invalid/item",
    title: str = "Item",
    source_artifact_path: str = "artifact.jsonl",
    blocked_reason: str | None = None,
) -> FreshnessObservation:
    return FreshnessObservation(
        source_id=source_id,
        item_id=item_id,
        source_url=source_url,
        title=title,
        content_hash=content_hash,
        retrieved_at_utc=retrieved_at_utc,
        source_tier="official" if source_id == OFFICIAL_GAZETTE_SOURCE_ID else "discovery",
        source_artifact_path=source_artifact_path,
        queue_source_track_id=42 if source_id == OFFICIAL_GAZETTE_SOURCE_ID else 43,
        blocked_reason=blocked_reason,
    )


def test_combine_observations_assigns_lifecycle_states_and_track_targets() -> None:
    observations = [
        _observation(
            OFFICIAL_GAZETTE_SOURCE_ID,
            "official-new",
            content_hash="a" * 64,
            title="New notice",
        ),
        _observation(
            OFFICIAL_GAZETTE_SOURCE_ID,
            "official-changed",
            content_hash="c" * 64,
            title="Changed notice",
        ),
        _observation(
            OFFICIAL_GAZETTE_SOURCE_ID,
            "official-unchanged",
            content_hash="d" * 64,
            title="Unchanged notice",
        ),
        _observation(
            OFFICIAL_GAZETTE_SOURCE_ID,
            "official-duplicate",
            content_hash="e" * 64,
            title="Duplicate notice",
        ),
        _observation(
            OFFICIAL_GAZETTE_SOURCE_ID,
            "official-duplicate",
            content_hash="e" * 64,
            title="Duplicate notice",
        ),
        _observation(
            OFFICIAL_GAZETTE_SOURCE_ID,
            "official-blocked",
            content_hash="f" * 64,
            title="Blocked notice",
            blocked_reason="unmapped_official_feed_url",
        ),
        _observation(
            DIGITALNZ_GAZETTE_SOURCE_ID,
            "digitalnz-new",
            content_hash="1" * 64,
            title="DigitalNZ notice",
        ),
    ]
    previous_lookup = {
        (OFFICIAL_GAZETTE_SOURCE_ID, "official-changed"): {
            "content_hash": "b" * 64,
            "first_seen_at_utc": "2026-07-01T00:00:00Z",
            "last_seen_at_utc": "2026-07-01T00:00:00Z",
            "retrieved_at_utc": "2026-07-01T00:00:00Z",
            "source_url": "https://example.invalid/changed",
            "title": "Changed notice",
            "source_artifact_path": "official/feed_state.jsonl",
        },
        (OFFICIAL_GAZETTE_SOURCE_ID, "official-unchanged"): {
            "content_hash": "d" * 64,
            "first_seen_at_utc": "2026-07-01T00:00:00Z",
            "last_seen_at_utc": "2026-07-01T00:00:00Z",
            "retrieved_at_utc": "2026-07-01T00:00:00Z",
            "source_url": "https://example.invalid/unchanged",
            "title": "Unchanged notice",
            "source_artifact_path": "official/feed_state.jsonl",
        },
        (OFFICIAL_GAZETTE_SOURCE_ID, "official-withdrawn"): {
            "content_hash": "w" * 64,
            "first_seen_at_utc": "2026-07-01T00:00:00Z",
            "last_seen_at_utc": "2026-07-01T00:00:00Z",
            "retrieved_at_utc": "2026-07-01T00:00:00Z",
            "source_url": "https://example.invalid/withdrawn",
            "title": "Withdrawn notice",
            "source_artifact_path": "official/feed_state.jsonl",
        },
        (DIGITALNZ_GAZETTE_SOURCE_ID, "digitalnz-deleted"): {
            "content_hash": "x" * 64,
            "first_seen_at_utc": "2026-07-01T00:00:00Z",
            "last_seen_at_utc": "2026-07-01T00:00:00Z",
            "retrieved_at_utc": "2026-07-01T00:00:00Z",
            "source_url": "https://example.invalid/deleted",
            "title": "Deleted notice",
            "source_artifact_path": "digitalnz/records.jsonl",
        },
        (DIGITALNZ_GAZETTE_SOURCE_ID, "digitalnz-unchanged"): {
            "content_hash": "y" * 64,
            "first_seen_at_utc": "2026-07-01T00:00:00Z",
            "last_seen_at_utc": "2026-07-01T00:00:00Z",
            "retrieved_at_utc": "2026-07-01T00:00:00Z",
            "source_url": "https://example.invalid/unchanged",
            "title": "DigitalNZ unchanged",
            "source_artifact_path": "digitalnz/records.jsonl",
        },
    }

    combined = _combine_observations(observations, previous_lookup)

    assert combined["state_counts"]["new"] == 3
    assert combined["state_counts"]["changed"] == 1
    assert combined["state_counts"]["unchanged"] == 1
    assert combined["state_counts"]["duplicate"] == 1
    assert combined["state_counts"]["blocked"] == 1
    assert combined["state_counts"]["withdrawn"] == 1
    assert combined["state_counts"]["deleted"] == 2

    queue_targets = {
        (row["source_id"], row["item_id"], row["target_track_id"])
        for row in combined["refresh_queue"]
    }
    assert (OFFICIAL_GAZETTE_SOURCE_ID, "official-new", 42) in queue_targets
    assert (OFFICIAL_GAZETTE_SOURCE_ID, "official-new", CANONICAL_TRACK_ID) in queue_targets
    assert (DIGITALNZ_GAZETTE_SOURCE_ID, "digitalnz-new", 43) in queue_targets
    assert (DIGITALNZ_GAZETTE_SOURCE_ID, "digitalnz-new", CANONICAL_TRACK_ID) in queue_targets
    assert (OFFICIAL_GAZETTE_SOURCE_ID, "official-blocked", 42) in queue_targets

    duplicate_rows = [
        row
        for row in combined["state_records"]
        if row["source_id"] == OFFICIAL_GAZETTE_SOURCE_ID and row["item_id"] == "official-duplicate"
    ]
    assert [row["status"] for row in duplicate_rows] == ["new", "duplicate"]


def test_build_gazette_freshness_report_writes_combined_and_source_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    official_feed = tmp_path / "official.xml"
    official_feed.write_text("<?xml version='1.0'?><rss version='2.0'><channel></channel></rss>", encoding="utf-8")

    official_rows = [
        {
            "id": "official-1",
            "url": "https://gazette.govt.nz/issues/2026-07-03/1.pdf",
            "title": "Official notice",
            "content_hash": "1" * 64,
            "retrieved_at": "2026-07-03T00:00:00Z",
            "mapping_status": "mapped",
        }
    ]

    def fake_write_feed_change_artifacts(output_dir, feed_xml, **kwargs):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "feed_state.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in official_rows) + "\n",
            encoding="utf-8",
        )
        (output_dir / "refresh_queue.jsonl").write_text("", encoding="utf-8")
        (output_dir / "review_candidates.jsonl").write_text("", encoding="utf-8")
        report = {
            "schema_version": "1.0",
            "generated_at_utc": "2026-07-03T00:00:00Z",
            "feed_url": kwargs.get("feed_url", ""),
            "item_count": len(official_rows),
            "state_records": official_rows,
            "refresh_queue": [],
            "review_candidates": [],
            "state_counts": {"mapped": 1},
            "source_counts": {OFFICIAL_GAZETTE_SOURCE_ID: 1},
            "queue_counts": {42: 1, CANONICAL_TRACK_ID: 1},
            "canonical_queue_count": 1,
            "source_queue_count": 1,
            "coverage_warning": "official",
        }
        (output_dir / "feed_change_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return report

    digitalnz_rows = [
        {
            "stable_id": "digitalnz-gazette-item-1",
            "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
            "source_url": "https://example.invalid/digitalnz-1.pdf",
            "landing_url": "https://digitalnz.org/records/1",
            "title": "DigitalNZ notice",
            "rights_note": "DigitalNZ rights statement",
            "content_sha256": "2" * 64,
            "retrieved_at": "2026-07-03T00:00:00Z",
            "coverage_state": "complete",
            "source_local_id": "digitalnz-gazette-item-1",
        }
    ]

    def fake_export_digitalnz_gazette_source(*, output_dir, api_key, **kwargs):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "records.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in digitalnz_rows) + "\n",
            encoding="utf-8",
        )
        (output_dir / "source_records.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in digitalnz_rows) + "\n",
            encoding="utf-8",
        )
        (output_dir / "manifests").mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": "1.0",
            "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
            "generated_at_utc": "2026-07-03T00:00:00Z",
            "manifest_sha256": "3" * 64,
            "content_sha256": "4" * 64,
        }
        (output_dir / "manifests" / "latest_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "_state").mkdir(parents=True, exist_ok=True)
        (output_dir / "_state" / "export_state.json").write_text(
            json.dumps({"query_sha256": "5" * 64}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {
            "ok": True,
            "records_path": str(output_dir / "records.jsonl"),
            "manifest_path": str(output_dir / "manifests" / "latest_manifest.json"),
            "state_path": str(output_dir / "_state" / "export_state.json"),
            "review": {"ok": True},
        }

    monkeypatch.setattr(
        "nz_legislation_corpus.gazette_freshness.write_feed_change_artifacts",
        fake_write_feed_change_artifacts,
    )
    monkeypatch.setattr(
        "nz_legislation_corpus.gazette_freshness.export_digitalnz_gazette_source",
        fake_export_digitalnz_gazette_source,
    )

    report = build_gazette_freshness_report(
        official_feed_path=official_feed,
        digitalnz_api_key="test-key",
        output_dir=tmp_path / "output",
        official_feed_url="https://gazette.govt.nz/issues",
        digitalnz_max_pages=1,
    )

    assert report["item_count"] == 2
    assert report["state_counts"]["new"] == 2
    assert report["queue_counts"][42] == 1
    assert report["queue_counts"][43] == 1
    assert report["queue_counts"][CANONICAL_TRACK_ID] == 2
    assert Path(report["state_path"]).exists()
    assert Path(report["queue_path"]).exists()
    assert Path(report["report_path"]).exists()
    assert Path(report["source_index_path"]).exists()
    assert (tmp_path / "output" / "official" / "feed_change_report.json").exists()
    assert (tmp_path / "output" / "digitalnz" / "manifests" / "latest_manifest.json").exists()
