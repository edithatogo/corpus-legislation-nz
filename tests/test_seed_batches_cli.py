from __future__ import annotations

import json
from pathlib import Path

from nz_legislation_corpus import cli
from nz_legislation_corpus.discovery import sha256_lines


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

    assert (output_dir / "historical-0001.txt").read_text(encoding="utf-8") == (
        "work-1\nwork-2\n"
    )
    assert (output_dir / "historical-0002.txt").read_text(encoding="utf-8") == "work-3\n"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["unique_record_count"] == 3
    assert manifest["batch_count"] == 2
    assert manifest["seed_sha256"] == sha256_lines(["work-1", "work-2", "work-3"])
