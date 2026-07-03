from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "nz_gazette_archive_staging.yml"
)
DOC_PATH = Path(__file__).resolve().parents[1] / "docs" / "nz_gazette_workflow_staging.md"


def _load_workflow() -> dict[str, object]:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_workflow_exists_and_is_manual_only() -> None:
    workflow = _load_workflow()
    dispatch = workflow.get("on") or workflow.get(True)

    assert workflow["name"] == "NZ Gazette archive staging"
    assert dispatch is not None
    dispatch = dispatch["workflow_dispatch"]
    assert dispatch["inputs"]
    assert "schedule" not in workflow
    assert False not in workflow

    inputs = dispatch["inputs"]
    assert set(inputs) >= {
        "stage_mode",
        "source_scope",
        "year",
        "comparison_run_id",
        "decisions_path",
        "minimum_free_gb",
        "publish_confirmed",
    }

    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["stage"]["steps"]


def test_workflow_contract_mentions_all_sources_and_publication_blocking() -> None:
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    workflow = _load_workflow()
    steps = workflow["jobs"]["stage"]["steps"]

    for source_id in (
        "official_gazette",
        "digitalnz_gazette",
        "victoria_lexisnexis_gazette",
        "nzlii_gazette",
    ):
        assert source_id in workflow_text

    assert "This workflow only stages review artifacts" in workflow_text
    assert any("Upload staging artifacts" in step.get("name", "") for step in steps)


def test_workflow_doc_exists_and_matches_staging_contract() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    for snippet in (
        ".github/workflows/nz_gazette_archive_staging.yml",
        "source archives",
        "canonical Gazette layer",
        "publish_confirmed",
        "External publication is disabled",
    ):
        assert snippet in text
