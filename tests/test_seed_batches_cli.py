from __future__ import annotations

import json
from pathlib import Path

import pytest

from nz_legislation_corpus import cli
from nz_legislation_corpus.discovery import sha256_lines


@pytest.mark.unit
def test_split_work_id_batches_writes_stable_batches(tmp_path: Path) -> None:
    seed_path = tmp_path / "reviewed-seed.txt"
    output_dir = tmp_path / "batches"
    manifest_path = tmp_path / "batch-manifest.json"
    seed_path.write_text(
        "\n".join(
            [
                "work-3",
                "work-1",
                "# comment",
                "work-2",
                "work-2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cli.split_work_id_batches_cmd(
        seed_work_ids=seed_path,
        output_dir=output_dir,
        batch_size=2,
        filename_prefix="historical",
        manifest_path=manifest_path,
    )

    assert (output_dir / "historical-0001.txt").read_text(encoding="utf-8") == ("work-1\nwork-2\n")
    assert (output_dir / "historical-0002.txt").read_text(encoding="utf-8") == "work-3\n"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["unique_record_count"] == 3
    assert manifest["batch_count"] == 2
    assert manifest["seed_sha256"] == sha256_lines(["work-1", "work-2", "work-3"])


@pytest.mark.unit
def test_reconcile_work_ids_writes_report_and_optional_merged_seed(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.txt"
    candidate = tmp_path / "candidate.txt"
    report_path = tmp_path / "reconciliation.json"
    merged_path = tmp_path / "merged.txt"
    baseline.write_text("work-2\nwork-1\n", encoding="utf-8")
    candidate.write_text("work-2\nwork-3\n", encoding="utf-8")

    cli.reconcile_work_ids_cmd(
        baseline_work_ids=baseline,
        candidate_work_ids=candidate,
        report_path=report_path,
        merged_output_path=merged_path,
        baseline_label="historical-bootstrap",
        candidate_label="expanded-discovery",
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["baseline_label"] == "historical-bootstrap"
    assert report["candidate_label"] == "expanded-discovery"
    assert report["added_work_ids"] == ["work-3"]
    assert report["removed_work_ids"] == ["work-1"]
    assert report["merged_sha256"] == sha256_lines(["work-1", "work-2", "work-3"])
    assert merged_path.read_text(encoding="utf-8") == "work-1\nwork-2\nwork-3\n"
    assert report["merged_sha256"] == sha256_lines(["work-1", "work-2", "work-3"])
    assert merged_path.read_text(encoding="utf-8") == "work-1\nwork-2\nwork-3\n"


@pytest.mark.unit
def test_split_batches_empty_file(tmp_path: Path) -> None:
    seed_path = tmp_path / "empty-seed.txt"
    output_dir = tmp_path / "batches"
    manifest_path = tmp_path / "batch-manifest.json"
    seed_path.write_text("", encoding="utf-8")

    cli.split_work_id_batches_cmd(
        seed_work_ids=seed_path,
        output_dir=output_dir,
        batch_size=2,
        filename_prefix="historical",
        manifest_path=manifest_path,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["unique_record_count"] == 0
    assert manifest["batch_count"] == 0
    assert manifest["seed_sha256"] == sha256_lines([])
    # Output dir is created but no batch files inside
    assert output_dir.exists()
    assert list(output_dir.iterdir()) == []  # no batch files


@pytest.mark.unit
def test_split_batches_batch_size_one(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.txt"
    output_dir = tmp_path / "batches"
    manifest_path = tmp_path / "batch-manifest.json"
    seed_path.write_text("work-a\nwork-b\nwork-c\n", encoding="utf-8")

    cli.split_work_id_batches_cmd(
        seed_work_ids=seed_path,
        output_dir=output_dir,
        batch_size=1,
        filename_prefix="single",
        manifest_path=manifest_path,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["unique_record_count"] == 3
    assert manifest["batch_count"] == 3
    assert manifest["batch_size"] == 1
    assert (output_dir / "single-0001.txt").read_text(encoding="utf-8") == "work-a\n"
    assert (output_dir / "single-0002.txt").read_text(encoding="utf-8") == "work-b\n"
    assert (output_dir / "single-0003.txt").read_text(encoding="utf-8") == "work-c\n"


@pytest.mark.unit
def test_split_batches_with_comments_and_blanks(tmp_path: Path) -> None:
    seed_path = tmp_path / "messy-seed.txt"
    output_dir = tmp_path / "batches"
    manifest_path = tmp_path / "batch-manifest.json"
    seed_path.write_text(
        "\n".join(
            [
                "",
                "# top-level comment",
                "",
                "  work-b  ",
                "",
                "# another comment",
                "work-a",
                "",
                "   # indented comment",
                "work-c",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cli.split_work_id_batches_cmd(
        seed_work_ids=seed_path,
        output_dir=output_dir,
        batch_size=2,
        filename_prefix="batch",
        manifest_path=manifest_path,
    )

    assert (output_dir / "batch-0001.txt").read_text(encoding="utf-8") == "work-a\nwork-b\n"
    assert (output_dir / "batch-0002.txt").read_text(encoding="utf-8") == "work-c\n"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["unique_record_count"] == 3
    assert manifest["batch_count"] == 2
