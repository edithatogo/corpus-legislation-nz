from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/target_weekly_legislation_cycle.yml")


def test_weekly_cycle_is_scheduled_pinned_and_full_inventory() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "17 16 * * 0"' in text
    assert "workflow_dispatch:" in text
    assert "d9abc05fa648f8b2049fb443477bc8f97691cf7f" in text
    assert 'BOOTSTRAP_RUN_ID: "32487223314"' in text
    assert "59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7" in text
    assert 'BATCH_SIZE: "500"' in text
    assert "--force-resync" in text
    assert 'harvest["works_attempted"] == 500' in text


def test_weekly_cycle_chains_and_verifies_complete_state() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--workflow target_weekly_legislation_cycle.yml" in text
    assert "--status success" in text
    assert 'prior_artifact="target-legislation-weekly-$prior_run_id"' in text
    assert "tools/verify_object_store.py" in text
    assert 'receipt["verified"] == receipt["object_count"]' in text
    assert "weekly-state-lineage.json" in text
    assert "target-legislation-weekly-${{ github.run_id }}" in text


def test_weekly_cycle_remains_fail_closed_and_non_publicating() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "actions: read\n  contents: read" in text
    assert "persist-credentials: false" in text
    assert "LEGISLATION_API_KEY: ${{ secrets.NZ_LEGISLATION_API_KEY }}" in text
    assert "if: always()" in text
    assert "HARVEST_EXIT_CODE" in text
    assert "RECONCILIATION_EXIT_CODE" in text
    assert "RECEIPT_VALIDATION_EXIT_CODE" in text
    assert "git push" not in text
    assert "HF_TOKEN" not in text
    assert "ZENODO" not in text
