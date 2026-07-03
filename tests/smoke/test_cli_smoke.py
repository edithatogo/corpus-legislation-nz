"""CLI smoke tests that exercise the full toolchain via typer.testing.CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nz_legislation_corpus.cli import app
from nz_legislation_corpus.utils import write_json, write_jsonl

runner = CliRunner()


@pytest.mark.smoke
def test_doctor_no_network() -> None:
    result = runner.invoke(app, ["doctor", "--no-network"])
    assert result.exit_code == 0, result.output
    # Doctor output shows [OK]/[WARN] checks
    assert "[WARN]" in result.output or "[OK]" in result.output
    assert "output_dir" in result.output


@pytest.mark.smoke
def test_doctor_help() -> None:
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0, result.output
    assert "doctor" in result.output


@pytest.mark.smoke
def test_smoke_fixture_creates_output(tmp_path: Path) -> None:
    result = runner.invoke(app, ["smoke-fixture", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "records.jsonl").exists()


@pytest.mark.smoke
def test_smoke_fixture_validate_chain(tmp_path: Path) -> None:
    result = runner.invoke(app, ["smoke-fixture", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "records.jsonl").exists()

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0, result.output


@pytest.mark.smoke
def test_smoke_manifest_after_fixture(tmp_path: Path) -> None:
    result = runner.invoke(app, ["smoke-fixture", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["manifest"])
    assert result.exit_code == 0, result.output
    manifest_path = tmp_path / "manifests" / "latest_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "manifest_sha256" in manifest


@pytest.mark.smoke
def test_smoke_coverage_report(tmp_path: Path) -> None:
    result = runner.invoke(app, ["smoke-fixture", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["coverage-report"])
    assert result.exit_code == 0, result.output
    coverage_path = tmp_path / "manifests" / "coverage_report.json"
    assert coverage_path.exists()


@pytest.mark.smoke
def test_manifest_empty_directory(tmp_path: Path) -> None:
    (tmp_path / "raw_xml").mkdir(parents=True)
    # The fixture env needs to point to tmp_path
    import os

    os.environ["NZLC_OUTPUT_DIR"] = str(tmp_path)

    result = runner.invoke(app, ["manifest"])
    assert result.exit_code == 0, result.output
    manifest_path = tmp_path / "manifests" / "latest_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["files"] == []


@pytest.mark.smoke
def test_top_level_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output


@pytest.mark.smoke
def test_validate_help() -> None:
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0, result.output


@pytest.mark.smoke
def test_manifest_help() -> None:
    result = runner.invoke(app, ["manifest", "--help"])
    assert result.exit_code == 0, result.output


@pytest.mark.smoke
def test_coverage_report_help() -> None:
    result = runner.invoke(app, ["coverage-report", "--help"])
    assert result.exit_code == 0, result.output


@pytest.mark.smoke
def test_gazette_freshness_detect_help() -> None:
    result = runner.invoke(app, ["gazette-freshness-detect", "--help"])
    assert result.exit_code == 0, result.output
    assert "gazette-freshness-detect" in result.output


@pytest.mark.smoke
def test_review_full_corpus_bootstrap_command(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_jsonl(data / "records.jsonl", [{"stable_id": "act_public_2026_26", "text": "text"}])
    write_json(data / "manifests" / "validation_report.json", {"ok": True})
    write_json(
        data / "manifests" / "latest_manifest.json",
        {"manifest_sha256": "abc123", "record_count": 1},
    )
    write_json(
        data / "manifests" / "coverage_report.json",
        {
            "record_count": 1,
            "risk_indicators": {
                "missing_text_records": 0,
                "missing_xml_url_records": 0,
                "ephemeral_identifier_records": 0,
            },
        },
    )
    write_json(
        data / "_state" / "sync_state.json",
        {"last_stats": {"records_failed": 0, "warnings": []}},
    )
    output_path = tmp_path / "review.json"

    result = runner.invoke(
        app,
        [
            "review-full-corpus-bootstrap",
            "--artifact-root",
            str(tmp_path),
            "--output-path",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(output_path.read_text(encoding="utf-8"))["ok"] is True


@pytest.mark.smoke
def test_split_work_id_periods_command(tmp_path: Path) -> None:
    seed_path = tmp_path / "work_ids.txt"
    seed_path.write_text("act_local_1889_1\nact_public_2020_1\nno-year-id\n", encoding="utf-8")
    output_dir = tmp_path / "periods"
    manifest_path = tmp_path / "periods" / "manifest.json"

    result = runner.invoke(
        app,
        [
            "split-work-id-periods",
            "--seed-work-ids",
            str(seed_path),
            "--output-dir",
            str(output_dir),
            "--manifest-path",
            str(manifest_path),
            "--api-boundary-year",
            "2020",
            "--api-boundary-source",
            "verified in smoke test",
            "--api-boundary-verified",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["api_boundary_verified"] is True
    assert (output_dir / "pre_1908.txt").exists()
    assert (output_dir / "year_2020.txt").exists()
    assert (output_dir / "unknown_year_review.txt").exists()


@pytest.mark.smoke
def test_smoke_fixture_help() -> None:
    result = runner.invoke(app, ["smoke-fixture", "--help"])
    assert result.exit_code == 0, result.output
