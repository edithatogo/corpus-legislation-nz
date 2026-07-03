from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate
from typer.testing import CliRunner

from nz_legislation_corpus.cli import app
from nz_legislation_corpus.nz_gazette_canonical import (
    build_nz_gazette_canonical_archive,
    build_nz_gazette_canonical_records,
    build_nz_gazette_canonical_review,
)


def _source_record(
    *,
    source_id: str,
    source_name: str,
    source_tier: str,
    stable_id: str,
    source_local_id: str,
    source_url: str,
    title: str,
    content_sha256: str,
    rights_note: str = "Gazette evidence layer.",
    publication_date: str = "2026-01-01",
    page_start: int = 1,
    page_end: int = 1,
    coverage_state: str = "complete",
) -> dict[str, object]:
    return {
        "stable_id": stable_id,
        "source_id": source_id,
        "source_name": source_name,
        "source_tier": source_tier,
        "record_kind": "issue_pdf",
        "source_url": source_url,
        "retrieval_method": "http-get",
        "retrieved_at": "2026-07-03T00:00:00Z",
        "content_sha256": content_sha256,
        "raw_artifact_path": f"raw/{stable_id}.pdf",
        "rights_note": rights_note,
        "source_local_id": source_local_id,
        "coverage_state": coverage_state,
        "extraction": {
            "title": title,
            "publication_date": publication_date,
            "page_start": page_start,
            "page_end": page_end,
            "normalized_text_sha256": content_sha256,
        },
        "provenance": {
            "pipeline_name": "nz-gazette-source",
            "pipeline_version": "1.0.0",
            "source_name": source_name,
            "source_record_id": source_local_id,
            "source_retrieved_at": "2026-07-03T00:00:00Z",
            "release_version": "1.0.0",
            "release_commit": "28a0624",
            "license_note": rights_note,
        },
    }


def _write_source_tree(
    root: Path,
    *,
    source_id: str,
    source_name: str,
    source_tier: str,
    records: list[dict[str, object]],
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "manifests").mkdir(parents=True, exist_ok=True)
    (root / "_state").mkdir(parents=True, exist_ok=True)
    for record in records:
        (root / "raw" / f"{record['stable_id']}.json").write_text(
            json.dumps(record, sort_keys=True), encoding="utf-8"
        )
    (root / "records.jsonl").write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "1.0",
        "source_id": source_id,
        "source_name": source_name,
        "source_tier": source_tier,
        "generated_at_utc": "2026-07-03T00:00:00Z",
        "record_count": len(records),
        "record_kind_counts": {"issue_pdf": len(records)},
        "coverage_state_counts": {"complete": len(records)},
        "records": records,
        "content_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
    }
    (root / "manifests" / "latest_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8"
    )
    (root / "_state" / "comparison_state.json").write_text(
        json.dumps({"source_id": source_id}, sort_keys=True), encoding="utf-8"
    )
    return root


def test_build_canonical_records_prefers_official_and_handles_metadata_only_matches(tmp_path: Path) -> None:
    official_dir = _write_source_tree(
        tmp_path / "data" / "official-gazette",
        source_id="official_gazette",
        source_name="NZ Gazette official website",
        source_tier="official",
        records=[
            _source_record(
                source_id="official_gazette",
                source_name="NZ Gazette official website",
                source_tier="official",
                stable_id="official-1",
                source_local_id="issue-a",
                source_url="https://gazette.govt.nz/issues/2026-01-01/issue-a.pdf",
                title="Notice A",
                content_sha256="a" * 64,
            )
        ],
    )
    digitalnz_dir = _write_source_tree(
        tmp_path / "data" / "digitalnz-gazette",
        source_id="digitalnz_gazette",
        source_name="DigitalNZ Gazette discovery/export",
        source_tier="discovery",
        records=[
            _source_record(
                source_id="digitalnz_gazette",
                source_name="DigitalNZ Gazette discovery/export",
                source_tier="discovery",
                stable_id="digitalnz-1",
                source_local_id="item-a",
                source_url="https://digitalnz.org/records/item-a",
                title="Notice A",
                content_sha256="a" * 64,
            )
        ],
    )
    historical_dir = _write_source_tree(
        tmp_path / "data" / "victoria-lexisnexis-gazette",
        source_id="victoria_lexisnexis_gazette",
        source_name="Victoria University / LexisNexis historical Gazette archive",
        source_tier="historical",
        records=[
            _source_record(
                source_id="victoria_lexisnexis_gazette",
                source_name="Victoria University / LexisNexis historical Gazette archive",
                source_tier="historical",
                stable_id="historical-1",
                source_local_id="2008-071",
                source_url="https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html#issue-071",
                title="Notice A",
                content_sha256="b" * 64,
                coverage_state="partial",
            )
        ],
    )

    comparison = build_nz_gazette_canonical_records(
        [
            {"source_id": "official_gazette", "source_dir": official_dir},
            {"source_id": "digitalnz_gazette", "source_dir": digitalnz_dir},
            {"source_id": "victoria_lexisnexis_gazette", "source_dir": historical_dir},
        ],
        comparison_run_id="gazette-compare-test-001",
    )
    canonical_schema = json.loads(
        (Path.cwd() / "schemas" / "nz_gazette_canonical_record.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert comparison["comparison_report"]["comparison_run_id"] == "gazette-compare-test-001"
    assert comparison["comparison_report"]["canonical_record_count"] == 2
    assert comparison["comparison_report"]["matched_record_count"] == 1
    assert comparison["comparison_report"]["historical_only_record_count"] == 1
    assert comparison["comparison_report"]["conflicting_record_count"] == 0

    canonical_records = comparison["canonical_records"]
    official_record = next(record for record in canonical_records if record["canonical_source"] == "official_gazette")
    historical_record = next(
        record for record in canonical_records if record["canonical_source"] == "victoria_lexisnexis_gazette"
    )
    validate(official_record, canonical_schema)
    validate(historical_record, canonical_schema)
    assert official_record["confidence"] == "high"
    assert historical_record["historical_only"] is True

    review = build_nz_gazette_canonical_review(
        canonical_records=canonical_records,
        conflict_queue=comparison["conflict_queue"],
    )
    assert review["ok"]


def test_build_canonical_review_requires_conflict_decisions(tmp_path: Path) -> None:
    official_dir = _write_source_tree(
        tmp_path / "data" / "official-gazette",
        source_id="official_gazette",
        source_name="NZ Gazette official website",
        source_tier="official",
        records=[
            _source_record(
                source_id="official_gazette",
                source_name="NZ Gazette official website",
                source_tier="official",
                stable_id="official-2",
                source_local_id="issue-b",
                source_url="https://gazette.govt.nz/issues/2026-01-02/issue-b.pdf",
                title="Official Title",
                content_sha256="c" * 64,
            )
        ],
    )
    digitalnz_dir = _write_source_tree(
        tmp_path / "data" / "digitalnz-gazette",
        source_id="digitalnz_gazette",
        source_name="DigitalNZ Gazette discovery/export",
        source_tier="discovery",
        records=[
            _source_record(
                source_id="digitalnz_gazette",
                source_name="DigitalNZ Gazette discovery/export",
                source_tier="discovery",
                stable_id="digitalnz-2",
                source_local_id="item-b",
                source_url="https://digitalnz.org/records/item-b",
                title="Different DigitalNZ Title",
                content_sha256="c" * 64,
            )
        ],
    )

    comparison = build_nz_gazette_canonical_records(
        [
            {"source_id": "official_gazette", "source_dir": official_dir},
            {"source_id": "digitalnz_gazette", "source_dir": digitalnz_dir},
        ],
        comparison_run_id="gazette-compare-test-002",
    )
    canonical_record = comparison["canonical_records"][0]
    review = build_nz_gazette_canonical_review(
        canonical_records=comparison["canonical_records"],
        conflict_queue=comparison["conflict_queue"],
    )
    assert not review["ok"]
    assert review["unresolved_conflict_count"] == 1

    decisions_path = tmp_path / "gazette_conflict_decisions.jsonl"
    decisions_path.write_text(
        json.dumps(
            {
                "decision_id": f"{canonical_record['canonical_id']}:title",
                "canonical_id": canonical_record["canonical_id"],
                "field_name": "title",
                "source_ids": ["official_gazette", "digitalnz_gazette"],
                "reviewer": "codex",
                "reviewed_at": "2026-07-03T00:00:00Z",
                "rationale": "Prefer official title.",
                "selected_value": "Official Title",
                "evidence_links": [str(official_dir / "records.jsonl")],
                "resolution_state": "accepted",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    comparison_with_decision = build_nz_gazette_canonical_records(
        [
            {"source_id": "official_gazette", "source_dir": official_dir},
            {"source_id": "digitalnz_gazette", "source_dir": digitalnz_dir},
        ],
        decisions=json.loads(decisions_path.read_text(encoding="utf-8").strip()) and [
            json.loads(decisions_path.read_text(encoding="utf-8").strip())
        ],
        comparison_run_id="gazette-compare-test-002",
    )
    reviewed = build_nz_gazette_canonical_review(
        canonical_records=comparison_with_decision["canonical_records"],
        conflict_queue=comparison_with_decision["conflict_queue"],
        decisions=[
            json.loads(decisions_path.read_text(encoding="utf-8").strip())
        ],
    )
    assert reviewed["ok"]


def test_canonical_archive_cli_handles_missing_source_tree(tmp_path: Path) -> None:
    official_dir = _write_source_tree(
        tmp_path / "data" / "official-gazette",
        source_id="official_gazette",
        source_name="NZ Gazette official website",
        source_tier="official",
        records=[
            _source_record(
                source_id="official_gazette",
                source_name="NZ Gazette official website",
                source_tier="official",
                stable_id="official-3",
                source_local_id="issue-c",
                source_url="https://gazette.govt.nz/issues/2026-01-03/issue-c.pdf",
                title="Notice C",
                content_sha256="d" * 64,
            )
        ],
    )
    digitalnz_dir = _write_source_tree(
        tmp_path / "data" / "digitalnz-gazette",
        source_id="digitalnz_gazette",
        source_name="DigitalNZ Gazette discovery/export",
        source_tier="discovery",
        records=[
            _source_record(
                source_id="digitalnz_gazette",
                source_name="DigitalNZ Gazette discovery/export",
                source_tier="discovery",
                stable_id="digitalnz-3",
                source_local_id="item-c",
                source_url="https://digitalnz.org/records/item-c",
                title="Notice C",
                content_sha256="d" * 64,
            )
        ],
    )

    archive = build_nz_gazette_canonical_archive(
        [
            {"source_id": "official_gazette", "source_dir": official_dir},
            {"source_id": "digitalnz_gazette", "source_dir": digitalnz_dir},
            {
                "source_id": "victoria_lexisnexis_gazette",
                "source_dir": tmp_path / "data" / "victoria-lexisnexis-gazette-missing",
            },
        ],
        tmp_path / "data" / "nz-gazette-canonical",
        year="2026",
        comparison_run_id="gazette-compare-test-003",
    )
    assert archive["ok"]
    assert archive["comparison_report"]["missing_source_count"] == 1

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "nz-gazette-canonical-archive",
            "--official-source-dir",
            str(official_dir),
            "--digitalnz-source-dir",
            str(digitalnz_dir),
            "--historical-source-dir",
            str(tmp_path / "data" / "victoria-lexisnexis-gazette-missing"),
            "--output-dir",
            str(tmp_path / "data" / "nz-gazette-canonical-cli"),
            "--year",
            "2026",
        ],
    )

    assert result.exit_code == 0, result.output
    assert any(
        path.name.endswith(".tar.zst") or path.name.endswith(".tar.gz")
        for path in (tmp_path / "dist" / "corpus-legislation-nz-gazette-canonical").iterdir()
    )
