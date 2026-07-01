from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW = Path(".github/workflows/official_feed_change_detection.yml")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _step_block(text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = text.index(marker)
    next_step = text.find("\n      - name: ", start + len(marker))
    return text[start:] if next_step == -1 else text[start:next_step]


@pytest.mark.unit
def test_feed_workflow_fails_closed_to_official_urls() -> None:
    text = _workflow_text()
    guard = _step_block(text, "Check feed URL")

    assert "NZLC_OFFICIAL_FEED_URL" in guard
    assert "https://*.legislation.govt.nz/*|https://legislation.govt.nz/*" in guard
    assert "Refusing non-official feed URL" in guard


@pytest.mark.unit
def test_feed_workflow_uploads_advisory_artifacts() -> None:
    text = _workflow_text()
    build = _step_block(text, "Build advisory refresh queue")
    upload = _step_block(text, "Upload feed change artifacts")

    assert "uv run nzlc feed-change-detect" in build
    assert "--previous-state-path" in build
    assert "name: official-feed-change-detection" in upload
    assert "generated/feed-change-detection/" in upload
