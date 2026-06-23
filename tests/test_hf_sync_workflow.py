from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW = Path(".github/workflows/hf_sync.yml")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _step_block(text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = text.index(marker)
    next_step = text.find("\n      - name: ", start + len(marker))
    return text[start:] if next_step == -1 else text[start:next_step]


@pytest.mark.unit
def test_hf_sync_restore_fails_closed() -> None:
    restore_block = _step_block(_workflow_text(), "Restore current live corpus from Hugging Face")

    assert "continue-on-error: true" not in restore_block
    assert "snapshot_download(" in restore_block


@pytest.mark.unit
def test_hf_sync_uploads_routine_maintenance_evidence() -> None:
    text = _workflow_text()
    evidence_block = _step_block(text, "Upload routine maintenance evidence")

    assert "uses: actions/upload-artifact@v4" in evidence_block
    assert "name: hf-sync-maintenance-evidence" in evidence_block
    assert "data/_state/sync_state.json" in evidence_block
    assert "data/manifests/latest_changes.json" in evidence_block
    assert "data/manifests/latest_manifest.json" in evidence_block
    assert "data/manifests/coverage_report.json" in evidence_block
    assert text.index("Verify uploaded manifest matches remote") < text.index(
        "Upload routine maintenance evidence"
    )
