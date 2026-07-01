from __future__ import annotations

from typing import Any

import pytest

from nz_legislation_corpus.website_fallback import (
    OfficialWebsiteFallbackPolicy,
    build_failed_record_retry_plan,
    build_fallback_attempt_provenance,
    build_playwright_diagnostics_plan,
    plan_failed_record_retries,
)


def _failed_record(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "record_id": "example-act-2026",
        "source_url": "https://www.legislation.govt.nz/act/public/2026/1/latest/DLM123456.html",
        "html_url": "https://www.legislation.govt.nz/act/public/2026-01-01/",
        "previous_failure_reason": "API XML and advertised HTML were unavailable",
    }
    record.update(overrides)
    return record


@pytest.mark.unit
def test_retry_plan_orders_official_fallback_attempts() -> None:
    plan = build_failed_record_retry_plan(
        _failed_record(),
        policy=OfficialWebsiteFallbackPolicy(allow_browser_rendering=True),
        retrieval_timestamp_utc="2026-07-01T00:00:00Z",
    )

    assert plan["status"] == "queued"
    assert plan["eligible"] is True
    assert plan["warning"].startswith("Official website fallback queued for example-act-2026")
    assert [attempt["retrieval_method"] for attempt in plan["attempts"]] == [
        "official_website_html",
        "official_website_alternate_dated_url",
        "official_website_rendered_html",
    ]
    assert plan["attempts"][0]["source_url"].startswith("https://www.legislation.govt.nz/")


@pytest.mark.unit
def test_retry_plan_fails_closed_without_public_official_url() -> None:
    plan = build_failed_record_retry_plan(
        _failed_record(
            source_url="https://example.invalid/act/public/2026/1/latest/DLM123456.html",
            html_url="https://example.invalid/act/public/2026-01-01/",
        ),
        policy=OfficialWebsiteFallbackPolicy(allow_browser_rendering=True),
        retrieval_timestamp_utc="2026-07-01T00:00:00Z",
    )

    assert plan["status"] == "blocked"
    assert plan["eligible"] is False
    assert plan["attempts"] == []
    assert "fail closed" in plan["warning"]
    assert "no eligible public official URL" in plan["warning"]


@pytest.mark.unit
def test_provenance_output_includes_hash_timestamp_and_failure_reason() -> None:
    provenance = build_fallback_attempt_provenance(
        source_url="https://www.legislation.govt.nz/act/public/2026-01-01/",
        retrieval_method="official_website_rendered_html",
        previous_failure_reason="API XML failed with HTTP 404",
        confidence="low",
        status="planned",
        content="rendered html body",
        retrieval_timestamp_utc="2026-07-01T00:00:00Z",
    )

    assert provenance == {
        "source_url": "https://www.legislation.govt.nz/act/public/2026-01-01/",
        "retrieval_method": "official_website_rendered_html",
        "retrieval_timestamp_utc": "2026-07-01T00:00:00Z",
        "content_hash": "025a22ed8f355ba953586fab65db44c66cf08451ed7e9a54a9c07bd53b910d88",
        "previous_failure_reason": "API XML failed with HTTP 404",
        "confidence": "low",
        "status": "planned",
    }


@pytest.mark.unit
def test_retry_planner_truncates_small_failed_set() -> None:
    report = plan_failed_record_retries(
        [
            _failed_record(record_id="record-1"),
            _failed_record(record_id="record-2"),
        ],
        policy=OfficialWebsiteFallbackPolicy(),
        max_records=1,
        retrieval_timestamp_utc="2026-07-01T00:00:00Z",
    )

    assert report["record_count"] == 2
    assert report["planned_count"] == 1
    assert report["blocked_count"] == 0
    assert any("Skipped 1 failed record" in warning for warning in report["warnings"])
    assert report["records"][0]["record_id"] == "record-1"


@pytest.mark.unit
def test_playwright_diagnostics_plan_writes_script_without_running_browser(tmp_path) -> None:
    retry_plan = plan_failed_record_retries(
        [_failed_record(canonical_url="https://www.legislation.govt.nz/act/public/2026/1/latest/")],
        policy=OfficialWebsiteFallbackPolicy(allow_browser_rendering=True),
        retrieval_timestamp_utc="2026-07-01T00:00:00Z",
    )

    plan = build_playwright_diagnostics_plan(retry_plan, output_dir=tmp_path)

    assert plan["execution"]["status"] == "not_run"
    assert plan["execution"]["requires_operator_approval"] is True
    assert plan["diagnostic_count"] == 1
    assert plan["diagnostics"][0]["retrieval_method"] == "official_website_rendered_html"
    assert (tmp_path / "playwright_diagnostics.mjs").exists()
    assert (tmp_path / "playwright_diagnostics_plan.json").exists()
    script = (tmp_path / "playwright_diagnostics.mjs").read_text(encoding="utf-8")
    assert "page.goto(item.source_url" in script
    assert "fullPage: true" in script
