from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW = Path(".github/workflows/monthly_full_reconciliation.yml")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _step_block(text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = text.index(marker)
    next_step = text.find("\n      - name: ", start + len(marker))
    return text[start:] if next_step == -1 else text[start:next_step]


@pytest.mark.unit
def test_monthly_reconciliation_schedule_has_safe_input_defaults() -> None:
    text = _workflow_text()
    env_block = text[text.index("    env:\n") : text.index("    steps:\n")]

    assert (
        "MIN_SECONDS_BETWEEN_REQUESTS: ${{ inputs.min_seconds_between_requests || '1.0' }}"
        in env_block
    )
    assert "MAX_WORKS: ${{ inputs.max_works || 'none' }}" in env_block

    disk_block = _step_block(text, "Check disk budget")
    assert "required_gb=\"${{ inputs.minimum_free_gb || '25' }}\"" in disk_block

    reconcile_block = _step_block(text, "Reconcile candidate seed")
    assert (
        "BASELINE_WORK_IDS_PATH: ${{ inputs.baseline_work_ids_path || 'seeds/work_ids.txt' }}"
        in reconcile_block
    )


@pytest.mark.unit
def test_monthly_reconciliation_upload_fails_closed() -> None:
    text = _workflow_text()
    guard_block = _step_block(text, "Refuse direct upload from monthly reconciliation")

    assert "if: ${{ inputs.upload_confirmed == true }}" in guard_block
    assert "Use Track 08 full_corpus_hf_upload.yml" in guard_block
    assert "Upload to live Hugging Face dataset after sync" not in text
