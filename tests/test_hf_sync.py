from __future__ import annotations

import subprocess
from pathlib import Path


def test_upload_large_folder_prunes_stale_managed_remote_files(
    tmp_path: Path, monkeypatch
) -> None:
    from nz_legislation_corpus import hf_sync

    (tmp_path / "parquet" / "legislation_type=act" / "year=2026").mkdir(
        parents=True
    )
    (
        tmp_path
        / "parquet"
        / "legislation_type=act"
        / "year=2026"
        / "part-00000.parquet"
    ).write_bytes(b"current")
    (tmp_path / "manifests").mkdir()
    (tmp_path / "manifests" / "latest_manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "records.jsonl").write_text("", encoding="utf-8")

    deleted: list[str] = []

    class FakeHfApi:
        def __init__(self, token: str | None = None) -> None:
            self.token = token

        def list_repo_files(
            self, repo_id: str, repo_type: str, revision: str
        ) -> list[str]:
            assert repo_id == "owner/dataset"
            assert repo_type == "dataset"
            assert revision == "main"
            return [
                "parquet/legislation_type=act/year=1955/part-00000.parquet",
                "parquet/legislation_type=act/year=2026/part-00000.parquet",
                "raw_xml/stale.xml",
                "unmanaged/keep.txt",
            ]

        def delete_file(
            self,
            path_in_repo: str,
            repo_id: str,
            *,
            repo_type: str,
            revision: str,
            commit_message: str,
        ) -> None:
            assert repo_id == "owner/dataset"
            assert repo_type == "dataset"
            assert revision == "main"
            assert commit_message.startswith("Prune stale NZ legislation corpus file:")
            deleted.append(path_in_repo)

    monkeypatch.setattr(hf_sync, "HfApi", FakeHfApi)
    monkeypatch.setattr(
        hf_sync.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="uploaded", stderr=""
        ),
    )

    result = hf_sync.upload_large_folder("owner/dataset", tmp_path, token="token")

    assert result == "uploaded\nPruned 2 stale managed file(s)."
    assert deleted == [
        "parquet/legislation_type=act/year=1955/part-00000.parquet",
        "raw_xml/stale.xml",
    ]
