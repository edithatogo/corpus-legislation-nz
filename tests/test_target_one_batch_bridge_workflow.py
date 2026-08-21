from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/target_one_batch_reconciliation.yml")


def test_target_one_batch_bridge_is_exact_and_artifact_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "5c17cecc41d65cd6d93a3ac4b61ac8e4d030af0c" in text
    assert "59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7" in text
    assert "--work-ids-file" in text
    assert "working-directory: target" in text
    assert "uv run --locked python tools/run_legislation_harvest.py" in text
    assert '--work-ids-file "../$BATCH_PATH"' in text
    assert "--expected-batch-sha256" in text
    assert "LEGISLATION_API_KEY: ${{ secrets.NZ_LEGISLATION_API_KEY }}" in text
    assert "permissions:\n  contents: read" in text
    assert "persist-credentials: false" in text
    assert "actions/upload-artifact@v4" in text
    assert "git push" not in text
    assert "HF_TOKEN" not in text
    assert "ZENODO" not in text


def test_target_one_batch_bridge_preserves_failure_evidence() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "id: harvest" in text
    assert "id: reconciliation" in text
    assert "if: always()" in text
    assert "HARVEST_EXIT_CODE" in text
    assert "RECONCILIATION_EXIT_CODE" in text
    assert text.index("Upload bounded target state and receipts") < text.index(
        "Enforce fail-closed outcome"
    )
