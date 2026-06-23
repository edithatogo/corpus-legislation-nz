from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW = Path(".github/workflows/full_corpus_hf_upload.yml")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _step_block(text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = text.index(marker)
    next_step = text.find("\n      - name: ", start + len(marker))
    return text[start:] if next_step == -1 else text[start:next_step]


@pytest.mark.unit
def test_full_corpus_upload_downloads_bootstrap_artifact_to_workspace_root() -> None:
    block = _step_block(_workflow_text(), "Download bootstrap artifact from Track 07")

    assert "          name: full-corpus-bootstrap-download\n" in block
    assert "          path: .\n" in block


@pytest.mark.unit
def test_full_corpus_upload_enforces_review_gate_before_publish() -> None:
    text = _workflow_text()
    review_block = _step_block(text, "Review full bootstrap artifact before publish")
    review_artifact_block = _step_block(text, "Upload review artifact before publish")

    assert "uv run nzlc review-full-corpus-bootstrap --artifact-root data" in review_block
    assert (
        "generated/full-corpus-bootstrap/review_report.json" in review_artifact_block
    )
    assert text.index("Review full bootstrap artifact before publish") < text.index(
        "Upload to live Hugging Face dataset"
    )


@pytest.mark.unit
def test_full_corpus_upload_requires_bootstrap_run_for_confirmed_publish() -> None:
    text = _workflow_text()
    guard_block = _step_block(
        text,
        "Require Track 07 artifact for confirmed full upload",
    )

    assert (
        "if: ${{ inputs.upload_confirmed == true && inputs.bootstrap_run_id == '' }}"
        in guard_block
    )
    assert "Confirmed full upload requires bootstrap_run_id" in guard_block
    assert text.index("Require Track 07 artifact for confirmed full upload") < text.index(
        "Upload to live Hugging Face dataset"
    )
