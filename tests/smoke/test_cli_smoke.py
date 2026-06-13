"""CLI smoke tests that exercise the full toolchain via typer.testing.CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nz_legislation_corpus.cli import app

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
def test_smoke_fixture_help() -> None:
    result = runner.invoke(app, ["smoke-fixture", "--help"])
    assert result.exit_code == 0, result.output
