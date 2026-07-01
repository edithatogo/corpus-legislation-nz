from __future__ import annotations

from nz_legislation_corpus.source_redundancy import (
    RetrievalAttempt,
    decide_source,
    summarize_source_redundancy,
)


def test_decide_source_prefers_canonical_api_over_fallback() -> None:
    fallback = RetrievalAttempt.from_content(
        source_name="NZ Legislation",
        url="https://www.legislation.govt.nz/act/public/1992/27/en/1992-04-10A/",
        method="alternate_dated_url",
        retrieved_at="2026-07-01T00:00:00Z",
        content="<html/>",
    )
    canonical = RetrievalAttempt.from_content(
        source_name="NZ Legislation API",
        url="https://api.example.invalid/version",
        method="api_xml",
        retrieved_at="2026-07-01T00:00:01Z",
        content="<xml/>",
        canonical=True,
    )

    decision = decide_source([fallback, canonical])

    assert decision.status == "canonical_api"
    assert decision.selected_method == "api_xml"
    assert decision.canonical is True
    assert decision.manual_review_required is False


def test_decide_source_marks_secondary_rescue_for_manual_review() -> None:
    rescue = RetrievalAttempt.from_content(
        source_name="NZLII",
        url="https://www.nzlii.org/nz/legis/hist_act/example.html",
        method="nzlii_rescue",
        retrieved_at="2026-07-01T00:00:00Z",
        content="rescued text",
        confidence="medium",
    )

    decision = decide_source([rescue])

    assert decision.status == "rescued_secondary"
    assert decision.canonical is False
    assert decision.manual_review_required is True


def test_summarize_source_redundancy_counts_review_records() -> None:
    records = [
        {
            "stable_id": "canonical",
            "source_redundancy": {
                "status": "canonical_api",
                "selected_source": "NZ Legislation API",
                "confidence": "high",
            },
        },
        {
            "stable_id": "rescued",
            "source_redundancy": {
                "status": "rescued_secondary",
                "selected_source": "NZLII",
                "confidence": "medium",
            },
        },
        {"stable_id": "no-metadata"},
    ]

    summary = summarize_source_redundancy(records)

    assert summary["records_with_source_redundancy"] == 2
    assert summary["status_counts"]["canonical_api"] == 1
    assert summary["status_counts"]["rescued_secondary"] == 1
    assert summary["manual_review_required_count"] == 1
    assert summary["manual_review_stable_ids"] == ["rescued"]
