from __future__ import annotations

from pathlib import Path

import pytest

from nz_legislation_corpus.nzlii_reconcile import (
    NZLII_SOURCE_INVENTORY,
    NZLIICandidateRecord,
    OfficialMetadataRecord,
    build_nzlii_reconciliation_report,
    classify_official_record,
    write_nzlii_reconciliation_report,
)


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
