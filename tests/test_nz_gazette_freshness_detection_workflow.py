from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "nz_gazette_freshness_detection.yml"
)
DOC_PATH = Path(__file__).resolve().parents[1] / "docs" / "nz_gazette_freshness_detection.md"


def _load_workflow() -> dict[str, object]:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_workflow_exists_and_is_manual_plus_scheduled() -> None:
    workflow = _load_workflow()
    dispatch = workflow.get("on") or workflow.get(True)

    assert workflow["name"] == "NZ Gazette freshness detection"
    assert dispatch is not None
    assert "workflow_dispatch" in dispatch
    assert "schedule" in dispatch
    assert workflow["permissions"] == {"contents": "read"}

    inputs = dispatch["workflow_dispatch"]["inputs"]
    assert set(inputs) >= {
        "official_feed_url",
        "previous_state_path",
        "digitalnz_max_pages",
    }


def test_workflow_contract_mentions_sources_and_freshness_outputs() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    workflow = _load_workflow()
    steps = workflow["jobs"]["detect"]["steps"]

    for snippet in (
        "official_feed_url",
        "DIGITALNZ_API_KEY",
        "gazette-freshness-detect",
        "generated/nz-gazette-freshness-detection/",
        "NZ Gazette freshness detection",
    ):
        assert snippet in text

    assert any("Download official feed" in step.get("name", "") for step in steps)
    assert any("Build freshness state and queues" in step.get("name", "") for step in steps)
    assert any("Upload freshness artifacts" in step.get("name", "") for step in steps)


def test_workflow_doc_exists_and_matches_freshness_contract() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    for snippet in (
        "Track 48",
        "freshness_state.jsonl",
        "refresh_queue.jsonl",
        "review_candidates.jsonl",
        "Track 42",
        "Track 46",
    ):
        assert snippet in text
