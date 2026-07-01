from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nz_legislation_corpus.cli import app
from nz_legislation_corpus.nzlii_reconcile import (
    NZLII_SOURCE_INVENTORY,
    NZLIICandidateRecord,
    OfficialMetadataRecord,
    build_nzlii_reconciliation_report,
    classify_official_record,
    write_nzlii_reconciliation_report,
)

runner = CliRunner()


def _candidate(
    *,
    url: str,
    title: str,
    date: str | None,
    content_hash: str,
    confidence: float = 0.5,
) -> NZLIICandidateRecord:
    return NZLIICandidateRecord(
        url=url,
        title=title,
        date=date,
        retrieved_at="2026-07-01T00:00:00Z",
        content_hash=content_hash,
        confidence=confidence,
        classification="missing",
    )


@pytest.mark.unit
def test_classify_exact_match_uses_title_date_and_hash() -> None:
    official = OfficialMetadataRecord(
        work_id="work-1",
        version_id="version-1",
        title="Test Act 2026",
        date="2026-06-30",
        content_hash="abc123",
    )
    candidate = _candidate(
        url="https://nzlii.example/act/test-act-2026",
        title="Test Act 2026",
        date="2026-06-30",
        content_hash="abc123",
        confidence=0.91,
    )

    result = classify_official_record(official, [candidate])

    assert result.classification == "exact"
    assert result.confidence == 1.0
    assert result.review_required is False
    assert result.selected_candidate is not None
    assert result.selected_candidate.url == candidate.url
    assert result.selected_candidate.title == candidate.title
    assert result.selected_candidate.retrieved_at == candidate.retrieved_at
    assert result.selected_candidate.content_hash == candidate.content_hash


@pytest.mark.unit
def test_classify_probable_match_flags_manual_review() -> None:
    official = OfficialMetadataRecord(
        work_id="work-2",
        title="Test Regulation 2026",
        date="2026-07-01",
    )
    candidate = _candidate(
        url="https://nzlii.example/reg/test-regulation-2026",
        title="Test Regulation 2026",
        date="2026-07-04",
        content_hash="def456",
        confidence=0.72,
    )

    result = classify_official_record(official, [candidate])

    assert result.classification == "probable"
    assert result.review_required is True
    assert result.selected_candidate is not None
    assert result.selected_candidate.url == candidate.url
    assert result.reason == "single_best_candidate_requires_manual_review"


@pytest.mark.unit
def test_classify_ambiguous_match_when_candidates_tie() -> None:
    official = OfficialMetadataRecord(
        work_id="work-3",
        version_id="version-3",
        title="Ambiguous Act",
        date="2026-07-01",
    )
    first = _candidate(
        url="https://nzlii.example/a",
        title="Ambiguous Act",
        date="2026-07-04",
        content_hash="aaa",
        confidence=0.71,
    )
    second = _candidate(
        url="https://nzlii.example/b",
        title="Ambiguous Act",
        date="2026-07-04",
        content_hash="bbb",
        confidence=0.71,
    )

    result = classify_official_record(official, [first, second])

    assert result.classification == "ambiguous"
    assert result.review_required is True
    assert len(result.candidate_matches) == 2
    assert {candidate.url for candidate in result.candidate_matches} == {
        first.url,
        second.url,
    }


@pytest.mark.unit
def test_classify_missing_match_when_no_candidates() -> None:
    official = OfficialMetadataRecord(work_id="work-4", title="Missing Act", date="2026-07-01")

    result = classify_official_record(official, [])

    assert result.classification == "missing"
    assert result.selected_candidate is None
    assert result.confidence == 0.0


@pytest.mark.unit
def test_classify_out_of_scope_record_short_circuits() -> None:
    official = OfficialMetadataRecord(
        work_id="work-5",
        title="External Material",
        date="2026-07-01",
        in_scope=False,
    )
    candidate = _candidate(
        url="https://nzlii.example/external",
        title="External Material",
        date="2026-07-01",
        content_hash="fff",
        confidence=0.99,
    )

    result = classify_official_record(official, [candidate])

    assert result.classification == "out_of_scope"
    assert result.review_required is False
    assert result.selected_candidate is None


@pytest.mark.unit
def test_build_nzlii_reconciliation_report_emits_manual_review_queue(tmp_path: Path) -> None:
    official_records = [
        OfficialMetadataRecord(
            work_id="work-1",
            version_id="version-1",
            title="Test Act 2026",
            date="2026-06-30",
            content_hash="abc123",
        ),
        OfficialMetadataRecord(
            work_id="work-2",
            title="Test Regulation 2026",
            date="2026-07-01",
        ),
        OfficialMetadataRecord(
            work_id="work-3",
            title="Ambiguous Act",
            date="2026-07-01",
        ),
        OfficialMetadataRecord(
            work_id="work-4",
            title="Missing Act",
            date="2026-07-01",
        ),
        OfficialMetadataRecord(
            work_id="work-5",
            title="External Material",
            date="2026-07-01",
            in_scope=False,
        ),
    ]
    candidate_groups = {
        "version-1": [
            _candidate(
                url="https://nzlii.example/act/test-act-2026",
                title="Test Act 2026",
                date="2026-06-30",
                content_hash="abc123",
                confidence=0.91,
            )
        ],
        "work-2": [
            _candidate(
                url="https://nzlii.example/reg/test-regulation-2026",
                title="Test Regulation 2026",
                date="2026-07-04",
                content_hash="def456",
                confidence=0.72,
            )
        ],
        "work-3": [
            _candidate(
                url="https://nzlii.example/a",
                title="Ambiguous Act",
                date="2026-07-04",
                content_hash="aaa",
                confidence=0.71,
            ),
            _candidate(
                url="https://nzlii.example/b",
                title="Ambiguous Act",
                date="2026-07-04",
                content_hash="bbb",
                confidence=0.71,
            ),
        ],
    }

    report = build_nzlii_reconciliation_report(
        official_records,
        candidate_groups,
        seed_work_ids=["work-1", "work-6"],
        bootstrap_failure_ids=["work-2", "work-4"],
    )
    output_path = tmp_path / "report.json"
    written = write_nzlii_reconciliation_report(
        output_path,
        official_records,
        candidate_groups,
        seed_work_ids=["work-1", "work-6"],
        bootstrap_failure_ids=["work-2", "work-4"],
    )

    assert report["source_role"] == "secondary_corroborating"
    assert report["source_inventory"] == NZLII_SOURCE_INVENTORY
    assert report["seed_comparison"]["seed_ids_missing_from_official_records"] == ["work-6"]
    assert report["bootstrap_failure_comparison"][
        "failed_ids_with_exact_or_probable_nzlii_candidate"
    ] == ["work-2"]
    assert report["text_rescue_triage_candidates"] == [
        {
            "official_work_id": "work-2",
            "official_version_id": None,
            "official_title": "Test Regulation 2026",
            "official_date": "2026-07-01",
            "classification": "probable",
            "confidence": 0.75,
            "fallback_status": "secondary_text_rescue_candidate_review_required",
            "source_role": "secondary_corroborating",
            "retrieval_method": "nzlii_text_rescue_candidate",
            "canonical_promotion_allowed": False,
            "review_required": True,
            "reason": (
                "Official bootstrap retrieval failed and NZLII has an exact/probable "
                "candidate. Treat as non-canonical review evidence only."
            ),
            "selected_candidate": {
                "url": "https://nzlii.example/reg/test-regulation-2026",
                "title": "Test Regulation 2026",
                "date": "2026-07-04",
                "retrieved_at": "2026-07-01T00:00:00Z",
                "content_hash": "def456",
                "confidence": 0.72,
                "classification": "probable",
            },
        }
    ]
    assert report["classification_counts"] == {
        "exact": 1,
        "probable": 1,
        "ambiguous": 1,
        "missing": 1,
        "out_of_scope": 1,
    }
    assert [row["classification"] for row in report["manual_review_candidates"]] == [
        "probable",
        "ambiguous",
    ]
    assert report["records"][0]["selected_candidate"] is not None
    assert (
        report["records"][0]["selected_candidate"]["url"]
        == "https://nzlii.example/act/test-act-2026"
    )
    assert report["records"][0]["selected_candidate"]["classification"] == "exact"
    assert report["records"][0]["selected_candidate"]["retrieved_at"] == "2026-07-01T00:00:00Z"
    assert report["records"][1]["review_required"] is True
    assert report["records"][1]["selected_candidate"]["classification"] == "probable"
    assert report["records"][2]["candidate_matches"][0]["classification"] == "ambiguous"
    assert report["records"][4]["classification"] == "out_of_scope"
    assert output_path.exists()
    assert written["official_record_count"] == 5


@pytest.mark.unit
def test_build_nzlii_reconciliation_report_preserves_failure_and_review_context() -> None:
    official_records = [
        OfficialMetadataRecord(
            work_id="work-2",
            title="Test Regulation 2026",
            date="2026-07-01",
        )
    ]
    candidate_groups = {
        "work-2": [
            _candidate(
                url="https://nzlii.example/reg/test-regulation-2026",
                title="Test Regulation 2026",
                date="2026-07-04",
                content_hash="def456",
                confidence=0.72,
            )
        ]
    }
    failure_record = {
        "work_id": "work-2",
        "source_url": "https://www.legislation.govt.nz/example",
        "failure_reason": "official_xml_404",
        "failed_at": "2026-07-01T01:00:00Z",
    }

    report = build_nzlii_reconciliation_report(
        official_records,
        candidate_groups,
        bootstrap_failure_records=[failure_record],
        review_report={
            "failed_records": [failure_record],
            "missing_records": [{"work_id": "work-9"}],
        },
    )

    assert report["bootstrap_failure_comparison"]["bootstrap_failure_records"] == [failure_record]
    assert report["review_report_comparison"] == {
        "review_report_supplied": True,
        "review_report_work_id_count": 2,
        "review_report_ids_with_exact_or_probable_nzlii_candidate": ["work-2"],
        "review_report_ids_missing_from_official_records": ["work-9"],
    }
    assert report["text_rescue_triage_candidates"][0]["bootstrap_failure"] == failure_record
    assert (
        report["text_rescue_triage_candidates"][0]["fallback_status"]
        == "secondary_text_rescue_candidate_review_required"
    )
    assert report["text_rescue_triage_candidates"][0]["canonical_promotion_allowed"] is False


@pytest.mark.unit
def test_reconcile_nzlii_cli_writes_report_with_rescue_provenance(tmp_path: Path) -> None:
    official_path = tmp_path / "official.jsonl"
    candidates_path = tmp_path / "candidates.json"
    failures_path = tmp_path / "failures.jsonl"
    review_path = tmp_path / "review.json"
    output_path = tmp_path / "report.json"

    official_path.write_text(
        json.dumps(
            {
                "work_id": "work-2",
                "title": "Test Regulation 2026",
                "date": "2026-07-01",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    candidates_path.write_text(
        json.dumps(
            {
                "work-2": [
                    {
                        "url": "https://nzlii.example/reg/test-regulation-2026",
                        "title": "Test Regulation 2026",
                        "date": "2026-07-04",
                        "retrieved_at": "2026-07-01T00:00:00Z",
                        "content_hash": "def456",
                        "confidence": 0.72,
                        "classification": "missing",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    failure_record = {"work_id": "work-2", "failure_reason": "official_xml_404"}
    failures_path.write_text(json.dumps(failure_record) + "\n", encoding="utf-8")
    review_path.write_text(
        json.dumps({"failed_records": [failure_record]}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "reconcile-nzlii",
            "--official-records-path",
            str(official_path),
            "--candidate-groups-path",
            str(candidates_path),
            "--bootstrap-failures-path",
            str(failures_path),
            "--review-report-path",
            str(review_path),
            "--output-path",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["review_report_comparison"]["review_report_supplied"] is True
    assert report["text_rescue_triage_candidates"][0]["bootstrap_failure"] == failure_record
    assert report["text_rescue_triage_candidates"][0]["review_required"] is True


@pytest.mark.unit
def test_nzlii_source_inventory_cli_writes_machine_readable_policy(tmp_path: Path) -> None:
    output_path = tmp_path / "source_inventory.json"

    result = runner.invoke(
        app,
        ["nzlii-source-inventory", "--output-path", str(output_path)],
    )

    assert result.exit_code == 0, result.output
    inventory = json.loads(output_path.read_text(encoding="utf-8"))
    assert inventory["source_role"] == "secondary_corroborating"
    assert inventory["sources"] == NZLII_SOURCE_INVENTORY
    assert inventory["sources"][0]["canonical_status"] == "not_canonical"
    assert (
        inventory["sources"][0]["access_policy"] == "conservative_manual_or_supplied_metadata_only"
    )
