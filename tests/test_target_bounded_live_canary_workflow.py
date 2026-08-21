from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/target_bounded_live_canary.yml")


def test_canary_is_pinned_bounded_and_state_authenticated() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "d9abc05fa648f8b2049fb443477bc8f97691cf7f" in text
    assert 'PRIOR_RUN_ID: "32477973065"' in text
    assert "a32dc371a1a47ae30a4afd58a9cbde2a439f3536d7705eb776e0fa68b4cd16db" in text
    assert "2abf0d8b76cc60e9b4e442724987b81848698dbdd98e56266f8726d468b33eaf" in text
    assert "ec71247b90e84d8c66f5d7fbd6283a9869abd647194feab22a4bc62510587743" in text
    assert 'BATCH_SIZE: "5"' in text
    assert "--force-resync" in text
    assert "--work-ids-file" in text
    assert 'works_attempted"] == 5' in text


def test_canary_is_fail_closed_artifact_only_and_non_publicating() -> None:
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
