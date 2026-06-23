from __future__ import annotations

import json
from pathlib import Path

import pytest

from nz_legislation_corpus.discovery import sha256_lines
from nz_legislation_corpus.period_shards import (
    assign_period,
    build_period_manifest,
    split_period_seed_files,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.unit
def test_assign_period_uses_coarse_historical_and_annual_recent_shards() -> None:
    assert assign_period(1889, api_boundary_year=2020) == "pre_1908"
    assert assign_period(1908, api_boundary_year=2020) == "1908_1949"
    assert assign_period(1979, api_boundary_year=2020) == "1950_1979"
    assert assign_period(1999, api_boundary_year=2020) == "1980_1999"
    assert assign_period(2000, api_boundary_year=2020) == "2000_2019"
    assert assign_period(2019, api_boundary_year=2020) == "2000_2019"
    assert assign_period(2020, api_boundary_year=2020) == "year_2020"
    assert assign_period(None, api_boundary_year=2020) == "unknown_year_review"


@pytest.mark.unit
def test_build_period_manifest_assigns_each_work_id_once() -> None:
    manifest = build_period_manifest(
        [
            "act_local_1889_1",
            "act_public_1908_1",
            "act_public_1950_1",
            "act_public_1980_1",
            "act_public_2001_1",
            "act_public_2020_1",
            "no-year-id",
        ],
        source_metadata={
            "act_public_2020_1": {"latest_version_id": "act_public_2020_1_en_2020-01-01"}
        },
        api_boundary_year=2020,
        api_boundary_source="verified in test fixture",
        api_boundary_verified=True,
    )

    assert manifest["source_record_count"] == 7
    assert manifest["unique_work_id_count"] == 7
    assert manifest["assigned_work_id_count"] == 7
    assert manifest["unassigned_work_ids"] == []
    assert manifest["duplicate_assignments"] == []
    assert manifest["api_boundary_verified"] is True
    assert manifest["api_boundary_decision"] == {
        "boundary_year": 2020,
        "source": "verified in test fixture",
        "verified": True,
        "status": "verified",
        "annual_shards_start_year": 2020,
        "warning": None,
    }
    assert manifest["seed_sha256"] == sha256_lines(
        [
            "act_local_1889_1",
            "act_public_1908_1",
            "act_public_1950_1",
            "act_public_1980_1",
            "act_public_2001_1",
            "act_public_2020_1",
            "no-year-id",
        ]
    )
    periods = {period["period_id"]: period for period in manifest["periods"]}
    assert periods["pre_1908"]["work_id_count"] == 1
    assert periods["1908_1949"]["work_id_count"] == 1
    assert periods["1950_1979"]["work_id_count"] == 1
    assert periods["1980_1999"]["work_id_count"] == 1
    assert periods["2000_2019"]["work_id_count"] == 1
    assert periods["year_2020"]["work_id_count"] == 1
    assert periods["unknown_year_review"]["work_id_count"] == 1


@pytest.mark.unit
def test_build_period_manifest_records_unverified_boundary_fallback() -> None:
    manifest = build_period_manifest(["act_public_2008_1"])

    assert manifest["api_boundary_year"] == 2008
    assert manifest["api_boundary_verified"] is False
    assert manifest["api_boundary_decision"] == {
        "boundary_year": 2008,
        "source": "planning_fallback_unverified",
        "verified": False,
        "status": "planning_fallback_unverified",
        "annual_shards_start_year": 2008,
        "warning": (
            "Annual recent shards start at the conservative planning fallback. "
            "Do not treat the API-native/recent boundary as verified until "
            "api_boundary_verified is true and api_boundary_source names the evidence."
        ),
    }


@pytest.mark.unit
def test_split_period_seed_files_writes_manifest_and_period_files(tmp_path: Path) -> None:
    seed_path = tmp_path / "work_ids.txt"
    seed_path.write_text(
        "\n".join(["act_local_1889_1", "act_public_2020_1", "no-year-id"]) + "\n",
        encoding="utf-8",
    )
    metadata_path = tmp_path / "provenance.json"
    metadata_path.write_text(
        json.dumps(
            {
                "works": [
                    {
                        "work_id": "act_public_2020_1",
                        "latest_version_id": "act_public_2020_1_en_2020-01-01",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "periods"
    manifest_path = tmp_path / "period-manifest.json"

    manifest = split_period_seed_files(
        seed_path,
        output_dir=output_dir,
        manifest_path=manifest_path,
        source_metadata_path=metadata_path,
        api_boundary_year=2020,
        api_boundary_source="verified in test fixture",
        api_boundary_verified=True,
    )

    assert manifest_path.exists()
    assert (output_dir / "pre_1908.txt").read_text(encoding="utf-8") == "act_local_1889_1\n"
    assert (output_dir / "year_2020.txt").read_text(encoding="utf-8") == "act_public_2020_1\n"
    assert (output_dir / "unknown_year_review.txt").read_text(encoding="utf-8") == "no-year-id\n"
    assert manifest["period_count"] == 3


@pytest.mark.unit
def test_period_bootstrap_workflow_carries_boundary_decision_context() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "full_corpus_period_bootstrap.yml"
    ).read_text(encoding="utf-8")

    assert '"api_boundary_decision": manifest["api_boundary_decision"]' in workflow
    assert '"period": period' in workflow
