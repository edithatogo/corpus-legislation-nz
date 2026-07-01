from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from nz_legislation_corpus.source_redundancy import (
    Confidence,
    RetrievalAttempt,
    decide_source,
    decision_from_record,
    summarize_source_redundancy,
)


def _attempt(
    method: str,
    *,
    confidence: Confidence = "high",
    canonical: bool = False,
) -> RetrievalAttempt:
    return RetrievalAttempt.from_content(
        source_name="NZ Legislation",
        url=f"https://example.invalid/{method}",
        method=method,
        retrieved_at="2026-07-01T00:00:00Z",
        content=f"{method} content",
        confidence=confidence,
        canonical=canonical,
    )


def test_decide_source_prefers_canonical_api_over_fallback() -> None:
    fallback = _attempt("alternate_dated_url")
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


def test_decide_source_priority_order_covers_all_fallback_states() -> None:
    attempts = [
        _attempt("nzlii_rescue", confidence="medium"),
        _attempt("nzlii_candidate", confidence="medium"),
        _attempt("official_website_rendered_html", confidence="low"),
        _attempt("alternate_dated_url"),
        _attempt("official_html"),
    ]

    decision = decide_source(attempts)

    assert decision.status == "official_html_fallback"
    assert decision.selected_method == "official_html"
    assert decision.canonical is True


def test_decide_source_does_not_promote_fallback_with_canonical_flag() -> None:
    fallback = _attempt("nzlii_rescue", confidence="medium", canonical=True)
    canonical = _attempt("official_html", confidence="high")

    decision = decide_source([fallback, canonical])

    assert decision.status == "official_html_fallback"
    assert decision.selected_method == "official_html"
    assert decision.canonical is True


def test_decide_source_marks_low_confidence_official_fallback_for_review() -> None:
    decision = decide_source([_attempt("official_html", confidence="low")])

    assert decision.status == "official_html_fallback"
    assert decision.canonical is True
    assert decision.manual_review_required is True


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


def test_decision_from_record_accepts_fallback_provenance_aliases() -> None:
    decision = decision_from_record(
        {
            "stable_id": "act_public_1992_27",
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
    )

    assert decision is not None
    assert decision.status == "official_website_fallback"
    assert decision.selected_url == "https://www.legislation.govt.nz/act/public/1992/27/latest/"
    assert decision.selected_method == "official_website_rendered_html"
    assert decision.manual_review_required is True
    assert decision.attempts[0].content_sha256 == "abc123"
    assert decision.attempts[0].warning == "API XML returned 404"


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
    assert summary["selected_method_counts"] == {}
    assert summary["fallback_method_counts"] == {}
    assert summary["confidence_counts"]["high"] == 1
    assert summary["confidence_counts"]["medium"] == 1
    assert summary["canonical_record_count"] == 1
    assert summary["fallback_or_secondary_record_count"] == 1
    assert summary["manual_review_required_count"] == 1
    assert summary["manual_review_stable_ids"] == ["rescued"]
    assert summary["resolver_decisions"] == [
        {
            "stable_id": "canonical",
            "status": "canonical_api",
            "selected_source": "NZ Legislation API",
            "selected_url": None,
            "selected_method": None,
            "confidence": "high",
            "canonical": True,
            "manual_review_required": False,
            "attempt_count": 0,
        },
        {
            "stable_id": "rescued",
            "status": "rescued_secondary",
            "selected_source": "NZLII",
            "selected_url": None,
            "selected_method": None,
            "confidence": "medium",
            "canonical": False,
            "manual_review_required": True,
            "attempt_count": 0,
        },
    ]


def test_summarize_source_redundancy_counts_fallback_methods() -> None:
    records = [
        {
            "stable_id": "html",
            "source_redundancy": {
                "attempts": [_attempt("official_html").to_dict()],
            },
        },
        {
            "stable_id": "alternate",
            "source_redundancy": {
                "attempts": [_attempt("alternate_dated_url").to_dict()],
            },
        },
        {
            "stable_id": "website",
            "source_redundancy": {
                "attempts": [
                    _attempt("official_website_rendered_html", confidence="low").to_dict()
                ],
            },
        },
        {
            "stable_id": "nzlii",
            "source_redundancy": {
                "attempts": [_attempt("nzlii_candidate", confidence="medium").to_dict()],
            },
        },
    ]

    summary = summarize_source_redundancy(records)

    assert summary["selected_method_counts"] == {
        "alternate_dated_url": 1,
        "nzlii_candidate": 1,
        "official_html": 1,
        "official_website_rendered_html": 1,
    }
    assert summary["fallback_method_counts"] == summary["selected_method_counts"]
    assert summary["manual_review_required_count"] == 2
    assert summary["manual_review_stable_ids"] == ["website", "nzlii"]


def test_source_decision_schema_accepts_resolver_output() -> None:
    schema_path = Path(__file__).parents[1] / "schemas" / "source_redundancy.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    decision = decide_source([_attempt("official_html")])
    first_hash = decision.attempts[0].content_sha256
    second_hash = _attempt("official_html").content_sha256

    validate(decision.to_dict(), schema)

    assert first_hash == second_hash


def test_source_decision_schema_accepts_null_retrieved_at() -> None:
    schema_path = Path(__file__).parents[1] / "schemas" / "source_redundancy.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    decision = decide_source(
        [
            RetrievalAttempt.from_content(
                source_name="NZ Legislation API",
                url="https://api.example.invalid/version",
                method="api_xml",
                retrieved_at=None,
                content="<xml/>",
                canonical=True,
            )
        ]
    )

    validate(decision.to_dict(), schema)

    assert decision.to_dict()["attempts"][0]["retrieved_at"] is None
