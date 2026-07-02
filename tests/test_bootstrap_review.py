from __future__ import annotations

import json
from pathlib import Path

import pytest

from nz_legislation_corpus.bootstrap_review import (
    build_full_corpus_bootstrap_review,
    write_full_corpus_bootstrap_review,
)
from nz_legislation_corpus.utils import write_json, write_jsonl


def _write_artifact(
    root: Path,
    *,
    records_failed: int = 0,
    records_deferred: int = 0,
    validation_ok: bool = True,
    manifest_record_count: int | None = None,
    risk_indicators: dict[str, int] | None = None,
    records: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
) -> None:
    data = root / "data"
    records = records or [
        {
            "stable_id": "act_public_2026_26",
            "title": "Test Act 2026",
            "text": "text",
            "xml_url": "https://example.invalid/act.xml",
        }
    ]
    write_jsonl(data / "records.jsonl", records)
    write_json(data / "manifests" / "validation_report.json", {"ok": validation_ok})
    write_json(
        data / "manifests" / "latest_manifest.json",
        {
            "manifest_sha256": "abc123",
            "record_count": manifest_record_count
            if manifest_record_count is not None
            else len(records),
        },
    )
    write_json(
        data / "manifests" / "coverage_report.json",
        {
            "record_count": len(records),
            "risk_indicators": risk_indicators
            or {
                "missing_text_records": 0,
                "missing_xml_url_records": 0,
                "ephemeral_identifier_records": 0,
            },
        },
    )
    warnings = list(warnings or [])
    if records_failed:
        warnings.append("version 123 failed: HTTP 404")
    if records_deferred:
        write_jsonl(
            data / "_state" / "metadata_only_deferred.jsonl",
            [
                {
                    "schema_version": "1.0",
                    "stable_id": "secondary-legislation_agency-drafted_2026_~123",
                    "reason": "metadata_only_no_downloadable_format",
                }
            ],
        )
    write_json(
        data / "_state" / "sync_state.json",
        {
            "last_stats": {
                "records_failed": records_failed,
                "records_deferred": records_deferred,
                "warnings": warnings,
            }
        },
    )


@pytest.mark.unit
def test_full_corpus_bootstrap_review_clean_artifact(tmp_path: Path) -> None:
    _write_artifact(tmp_path)

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["ok"] is True
    assert report["missing_artifacts"] == []
    assert report["records_jsonl_count"] == 1
    assert report["validation_ok"] is True
    assert report["manifest_sha256"] == "abc123"
    assert report["records_failed"] == 0
    assert report["triage_required"] is False


@pytest.mark.unit
def test_full_corpus_bootstrap_review_flags_failures(tmp_path: Path) -> None:
    _write_artifact(tmp_path, records_failed=1)

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["ok"] is False
    assert report["records_failed"] == 1
    assert report["failed_version_warnings"] == ["version 123 failed: HTTP 404"]
    assert report["triage_required"] is True


@pytest.mark.unit
def test_full_corpus_bootstrap_review_surfaces_deferred_metadata(
    tmp_path: Path,
) -> None:
    _write_artifact(tmp_path, records_deferred=1)

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["ok"] is True
    assert report["records_deferred"] == 1
    assert report["deferred_metadata_count"] == 1
    assert report["deferred_metadata_stable_ids"] == [
        "secondary-legislation_agency-drafted_2026_~123"
    ]
    assert report["triage_required"] is False


@pytest.mark.unit
def test_full_corpus_bootstrap_review_surfaces_browser_fallback_provenance(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        records=[
            {
                "stable_id": "act_public_1992_27",
                "title": "Fallback Act",
                "text": "text",
                "xml_url": "https://www.legislation.govt.nz/act/public/1992/27/latest.xml",
                "source_redundancy": {
                    "attempts": [
                        {
                            "source_name": "NZ Legislation",
                            "source_url": "https://www.legislation.govt.nz/act/public/1992/27/latest/",
                            "retrieval_method": "official_website_rendered_html",
                            "retrieval_timestamp_utc": "2026-07-01T00:00:00Z",
                            "content_hash": "abc123",
                            "previous_failure_reason": "API XML returned 404",
                            "confidence": "low",
                            "status": "success",
                        }
                    ]
                },
            }
        ],
        warnings=["browser fallback queued for act_public_1992_27 after API XML returned 404"],
    )

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["browser_fallback_warning_count"] == 1
    assert report["browser_fallback_warnings"] == [
        "browser fallback queued for act_public_1992_27 after API XML returned 404"
    ]
    assert report["browser_fallback_provenance_count"] == 1
    assert report["browser_fallback_provenance"] == [
        {
            "stable_id": "act_public_1992_27",
            "source_url": "https://www.legislation.govt.nz/act/public/1992/27/latest/",
            "retrieval_method": "official_website_rendered_html",
            "retrieval_timestamp_utc": "2026-07-01T00:00:00Z",
            "content_hash": "abc123",
            "previous_failure_reason": "API XML returned 404",
            "confidence": "low",
            "status": "success",
            "rights_note": (
                "Official website rendered diagnostics are for manual triage only; "
                "they are not canonical corpus content."
            ),
        }
    ]
    assert report["source_redundancy"]["selected_method_counts"] == {
        "official_website_rendered_html": 1
    }
    assert report["source_redundancy"]["fallback_method_counts"] == {
        "official_website_rendered_html": 1
    }
    assert report["source_redundancy"]["manual_review_stable_ids"] == ["act_public_1992_27"]
    assert report["source_redundancy"]["resolver_decisions"][0]["status"] == (
        "official_website_fallback"
    )


@pytest.mark.unit
def test_full_corpus_bootstrap_review_flags_manifest_count_mismatch(
    tmp_path: Path,
) -> None:
    _write_artifact(tmp_path, manifest_record_count=2)

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["ok"] is False
    assert report["records_jsonl_count"] == 1
    assert report["manifest_record_count"] == 2
    assert report["triage_required"] is True


@pytest.mark.unit
def test_full_corpus_bootstrap_review_flags_risk_indicators(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        risk_indicators={
            "missing_text_records": 1,
            "missing_xml_url_records": 1,
            "ephemeral_identifier_records": 1,
        },
    )

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["ok"] is False
    assert report["risk_indicators"] == {
        "missing_text_records": 1,
        "missing_xml_url_records": 1,
        "ephemeral_identifier_records": 1,
    }
    assert report["triage_required"] is True


@pytest.mark.unit
def test_full_corpus_bootstrap_review_writes_report(tmp_path: Path) -> None:
    _write_artifact(tmp_path)
    output_path = tmp_path / "review.json"

    report = write_full_corpus_bootstrap_review(tmp_path, output_path)

    assert report["ok"] is True
    assert json.loads(output_path.read_text(encoding="utf-8"))["ok"] is True


@pytest.mark.unit
def test_full_corpus_bootstrap_review_includes_period_context(tmp_path: Path) -> None:
    _write_artifact(tmp_path)
    write_json(
        tmp_path / "generated" / "full-corpus-periods" / "period_context.json",
        {"period_id": "year_2020", "work_id_count": 1},
    )

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["period_context"] == {"period_id": "year_2020", "work_id_count": 1}
    assert report["period_quality"] == {
        "period_id": "year_2020",
        "work_id_count": 1,
        "record_count": 1,
        "validation_ok": True,
        "manifest_sha256": "abc123",
        "records_failed": 0,
        "records_deferred": 0,
        "risk_indicators": {
            "missing_text_records": 0,
            "missing_xml_url_records": 0,
            "ephemeral_identifier_records": 0,
        },
        "ok": True,
        "triage_required": False,
        "api_boundary_decision": None,
    }


@pytest.mark.unit
def test_full_corpus_bootstrap_review_reads_nested_period_work_id_count(
    tmp_path: Path,
) -> None:
    _write_artifact(tmp_path)
    write_json(
        tmp_path / "generated" / "full-corpus-periods" / "period_context.json",
        {
            "period_id": "year_2020",
            "period": {"period_id": "year_2020", "work_id_count": 3},
            "api_boundary_decision": {
                "boundary_year": 2008,
                "verified": False,
                "status": "planning_fallback_unverified",
            },
        },
    )

    report = build_full_corpus_bootstrap_review(tmp_path)

    assert report["period_quality"]["work_id_count"] == 3
    assert report["period_quality"]["api_boundary_decision"] == {
        "boundary_year": 2008,
        "verified": False,
        "status": "planning_fallback_unverified",
    }
