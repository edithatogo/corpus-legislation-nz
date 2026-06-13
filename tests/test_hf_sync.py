from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.mark.unit
def test_upload_large_folder_prunes_stale_managed_remote_files(tmp_path: Path, monkeypatch) -> None:
    from nz_legislation_corpus import hf_sync

    (tmp_path / "parquet" / "legislation_type=act" / "year=2026").mkdir(parents=True)
    (
        tmp_path / "parquet" / "legislation_type=act" / "year=2026" / "part-00000.parquet"
    ).write_bytes(b"current")
    (tmp_path / "manifests").mkdir()
    (tmp_path / "manifests" / "latest_manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "records.jsonl").write_text("", encoding="utf-8")

    deleted: list[str] = []

    class FakeHfApi:
        def __init__(self, token: str | None = None) -> None:
            self.token = token

        def list_repo_files(self, repo_id: str, repo_type: str, revision: str) -> list[str]:
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


@pytest.mark.unit
def test_is_managed_remote_path() -> None:
    from nz_legislation_corpus.hf_sync import _is_managed_remote_path

    # Managed root files
    assert _is_managed_remote_path("README.md") is True
    assert _is_managed_remote_path("records.jsonl") is True

    # Managed prefixes
    assert _is_managed_remote_path("_state/sync_state.json") is True
    assert _is_managed_remote_path("manifests/latest_manifest.json") is True
    assert (
        _is_managed_remote_path("parquet/legislation_type=act/year=2026/part-00000.parquet") is True
    )
    assert _is_managed_remote_path("raw_xml/some_file.xml") is True

    # Unmanaged paths
    assert _is_managed_remote_path(".git/config") is False
    assert _is_managed_remote_path("unmanaged/keep.txt") is False
    assert _is_managed_remote_path("cache/huggingface/tmp") is False


@pytest.mark.unit
def test_local_repo_paths(tmp_path: Path) -> None:
    from nz_legislation_corpus.hf_sync import _local_repo_paths

    (tmp_path / "parquet" / "year=2026").mkdir(parents=True)
    (tmp_path / "parquet" / "year=2026" / "part-00000.parquet").write_bytes(b"data")
    (tmp_path / "records.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "manifests").mkdir()
    (tmp_path / "manifests" / "latest_manifest.json").write_text("{}", encoding="utf-8")
    # Excluded by DEFAULT_EXCLUDES (patterns that work with Path.match)
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "compiled.pyc").write_bytes(b"x")
    (tmp_path / ".DS_Store").write_bytes(b"x")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("", encoding="utf-8")
    (tmp_path / ".ruff_cache").mkdir()
    (tmp_path / ".ruff_cache" / "cache.db").write_bytes(b"x")
    # Non-excluded files in the tree
    (tmp_path / "raw_xml").mkdir()
    (tmp_path / "raw_xml" / "doc.xml").write_text("<doc/>", encoding="utf-8")

    paths = _local_repo_paths(tmp_path)

    # Managed files should be present
    assert "parquet/year=2026/part-00000.parquet" in paths
    assert "records.jsonl" in paths
    assert "manifests/latest_manifest.json" in paths
    assert "raw_xml/doc.xml" in paths
    # Files matching exclude patterns should be absent
    assert "__pycache__/compiled.pyc" not in paths
    assert ".DS_Store" not in paths
    assert ".git/config" not in paths


@pytest.mark.unit
def test_local_repo_paths_empty_dir(tmp_path: Path) -> None:
    from nz_legislation_corpus.hf_sync import _local_repo_paths

    paths = _local_repo_paths(tmp_path)
    assert paths == set()


@pytest.mark.unit
def test_stale_remote_paths_with_mocked_api(tmp_path: Path, monkeypatch) -> None:
    from nz_legislation_corpus import hf_sync

    (tmp_path / "records.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "parquet" / "year=2026").mkdir(parents=True)
    (tmp_path / "parquet" / "year=2026" / "part-00000.parquet").write_bytes(b"current")

    class FakeListApi:
        def __init__(self, token: str | None = None) -> None:
            self.token = token

        def list_repo_files(self, repo_id: str, repo_type: str, revision: str) -> list[str]:
            return [
                "parquet/year=2026/part-00000.parquet",  # still present locally
                "parquet/year=1955/part-00000.parquet",  # stale, managed
                "raw_xml/stale.xml",  # stale, managed
                "unmanaged/keep.txt",  # unmanaged, should stay
            ]

    monkeypatch.setattr(hf_sync, "HfApi", FakeListApi)

    stale = hf_sync._stale_remote_paths("owner/dataset", tmp_path, token="token", revision="main")

    assert stale == [
        "parquet/year=1955/part-00000.parquet",
        "raw_xml/stale.xml",
    ]


@pytest.mark.unit
def test_stale_remote_paths_repo_not_found(tmp_path: Path, monkeypatch) -> None:
    from huggingface_hub.utils import RepositoryNotFoundError

    from nz_legislation_corpus import hf_sync

    class FakeApiNotFound:
        def __init__(self, token: str | None = None) -> None:
            self.token = token

        def list_repo_files(self, repo_id: str, repo_type: str, revision: str) -> list[str]:
            # Build a minimal fake response object that satisfies RepositoryNotFoundError
            import httpx

            resp = httpx.Response(
                status_code=404,
                content=b'{"error": "Not found"}',
                headers={"Content-Type": "application/json"},
                request=httpx.Request("GET", f"https://huggingface.co/api/datasets/{repo_id}"),
            )
            raise RepositoryNotFoundError("Not found", response=resp)

    monkeypatch.setattr(hf_sync, "HfApi", FakeApiNotFound)

    stale = hf_sync._stale_remote_paths("missing/repo", tmp_path, token="token")
    assert stale == []


@pytest.mark.unit
def test_default_excludes_cover_common_patterns() -> None:
    from nz_legislation_corpus.hf_sync import DEFAULT_EXCLUDES

    assert ".git/**" in DEFAULT_EXCLUDES
    assert "**/.DS_Store" in DEFAULT_EXCLUDES
    assert "**/__pycache__/**" in DEFAULT_EXCLUDES
    assert "**/*.pyc" in DEFAULT_EXCLUDES
    assert ".pytest_cache/**" in DEFAULT_EXCLUDES
    assert ".ruff_cache/**" in DEFAULT_EXCLUDES
    assert "cache/huggingface/**" in DEFAULT_EXCLUDES
    assert ".cache/**" in DEFAULT_EXCLUDES
