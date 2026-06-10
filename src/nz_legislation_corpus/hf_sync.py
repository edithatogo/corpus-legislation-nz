from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError

from .utils import read_json

DEFAULT_EXCLUDES = [
    ".git/**",
    "**/.DS_Store",
    "**/__pycache__/**",
    "**/*.pyc",
    ".pytest_cache/**",
    ".ruff_cache/**",
    "cache/huggingface/**",
    ".cache/**",
]

MANAGED_PATH_PREFIXES = (
    "_state/",
    "manifests/",
    "parquet/",
    "raw_xml/",
)

MANAGED_ROOT_FILES = {
    "README.md",
    "records.jsonl",
}


def remote_manifest(
    repo_id: str, *, token: str | None = None, revision: str = "main"
) -> dict[str, Any] | None:
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename="manifests/latest_manifest.json",
            repo_type="dataset",
            token=token,
            revision=revision,
        )
        return read_json(Path(path), default=None)
    except (EntryNotFoundError, RepositoryNotFoundError, FileNotFoundError):
        return None


def create_dataset_repo_if_needed(
    repo_id: str, *, token: str | None = None, private: bool = False
) -> None:
    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=private, exist_ok=True)


def _is_managed_remote_path(path: str) -> bool:
    return path in MANAGED_ROOT_FILES or path.startswith(MANAGED_PATH_PREFIXES)


def _local_repo_paths(folder: Path) -> set[str]:
    paths: set[str] = set()
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(folder).as_posix()
        if any(path.match(pattern) for pattern in DEFAULT_EXCLUDES):
            continue
        paths.add(rel)
    return paths


def _stale_remote_paths(
    repo_id: str,
    folder: Path,
    *,
    token: str | None = None,
    revision: str = "main",
) -> list[str]:
    api = HfApi(token=token)
    try:
        remote_paths = api.list_repo_files(repo_id=repo_id, repo_type="dataset", revision=revision)
    except RepositoryNotFoundError:
        return []
    local_paths = _local_repo_paths(folder)
    return sorted(
        path for path in remote_paths if _is_managed_remote_path(path) and path not in local_paths
    )


def prune_stale_remote_paths(
    repo_id: str,
    stale_paths: list[str],
    *,
    token: str | None = None,
    revision: str = "main",
) -> int:
    if not stale_paths:
        return 0
    api = HfApi(token=token)
    for path in stale_paths:
        try:
            api.delete_file(
                path_in_repo=path,
                repo_id=repo_id,
                repo_type="dataset",
                revision=revision,
                commit_message=f"Prune stale NZ legislation corpus file: {path}",
            )
        except EntryNotFoundError:
            continue
    return len(stale_paths)


def upload_large_folder(
    repo_id: str,
    folder: Path,
    *,
    token: str | None = None,
    revision: str = "main",
    quiet: bool = True,
    num_workers: int | None = None,
    prune: bool = True,
) -> str:
    """Upload with `hf upload-large-folder`, falling back to HfApi.upload_folder.

    `hf_xet` is enabled by default in modern huggingface_hub. HF_XET_HIGH_PERFORMANCE=1
    requests the high-throughput path without the deprecated hf_transfer flag.
    """
    env = os.environ.copy()
    if token:
        env["HF_TOKEN"] = token
    env.setdefault("HF_XET_HIGH_PERFORMANCE", "1")

    cmd = [
        "hf",
        "upload-large-folder",
        repo_id,
        str(folder),
        "--repo-type",
        "dataset",
        "--revision",
        revision,
    ]
    if quiet:
        cmd.extend(["--format", "quiet"])
    if num_workers:
        cmd.extend(["--num-workers", str(num_workers)])
    for pattern in DEFAULT_EXCLUDES:
        cmd.extend(["--exclude", pattern])
    stale_paths = (
        _stale_remote_paths(repo_id, folder, token=token, revision=revision) if prune else []
    )
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True, env=env)
        url = (
            result.stdout.strip()
            or result.stderr.strip()
            or f"https://huggingface.co/datasets/{repo_id}/tree/{revision}"
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        api = HfApi(token=token)
        api.upload_folder(
            repo_id=repo_id,
            repo_type="dataset",
            folder_path=str(folder),
            path_in_repo=".",
            revision=revision,
            commit_message="Sync NZ legislation corpus",
            ignore_patterns=DEFAULT_EXCLUDES,
        )
        url = f"https://huggingface.co/datasets/{repo_id}/tree/{revision}"
    pruned = prune_stale_remote_paths(repo_id, stale_paths, token=token, revision=revision)
    if pruned:
        return f"{url}\nPruned {pruned} stale managed file(s)."
    return url
