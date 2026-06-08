from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .schema import RECORD_SCHEMA_ID, RECORD_SCHEMA_VERSION
from .utils import sha256_file, sha256_text, utc_now_iso, write_json

_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "cache",
    ".cache",
}
_EXCLUDED_TOP_LEVEL_DIRS = {"manifests", "_state"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
_EXCLUDED_NAMES = {".DS_Store"}


def _record_count_from_jsonl(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).replace(microsecond=0).isoformat()


def _should_exclude(root_dir: Path, path: Path) -> bool:
    rel = path.relative_to(root_dir)
    parts = set(rel.parts)
    if parts & _EXCLUDED_DIRS:
        return True
    if rel.parts and rel.parts[0] in _EXCLUDED_TOP_LEVEL_DIRS:
        return True
    if path.name in _EXCLUDED_NAMES:
        return True
    return path.suffix in _EXCLUDED_SUFFIXES


def _content_signature_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the stable, content-only subset used to decide whether the corpus changed.

    This deliberately excludes generated timestamps, local state, validation reports, manifests,
    caches, and modified times. Those fields are useful diagnostics but must not force a new
    Hugging Face upload on every scheduled run.
    """
    return {
        "schema_version": payload.get("schema_version"),
        "pipeline_schema": payload.get("pipeline_schema"),
        "record_count": payload.get("record_count"),
        "files": [
            {"path": f["path"], "size_bytes": f["size_bytes"], "sha256": f["sha256"]}
            for f in payload.get("files", [])
        ],
    }


def build_manifest(root_dir: Path, *, manifest_path: Path | None = None) -> dict[str, Any]:
    root_dir = Path(root_dir)
    files: list[dict[str, Any]] = []
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue
        if _should_exclude(root_dir, path):
            continue
        rel = path.relative_to(root_dir).as_posix()
        stat = path.stat()
        files.append(
            {
                "path": rel,
                "size_bytes": stat.st_size,
                "sha256": sha256_file(path),
                "modified_time_utc": _mtime_utc(path),
            }
        )
    payload = {
        "schema_version": "1.1",
        "pipeline_schema": "nzlc-manifest-v1",
        "record_schema": RECORD_SCHEMA_ID,
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "generated_at_utc": utc_now_iso(),
        "pipeline_version": os.getenv("GITHUB_SHA", "local-dev"),
        "github_repository": os.getenv("GITHUB_REPOSITORY", ""),
        "github_run_id": os.getenv("GITHUB_RUN_ID", ""),
        "hf_repo_id": os.getenv("HF_REPO_ID", ""),
        "record_count": _record_count_from_jsonl(root_dir / "records.jsonl"),
        "files": files,
    }
    content_payload = _content_signature_payload(payload)
    payload["content_sha256"] = sha256_text(
        json.dumps(content_payload, sort_keys=True, ensure_ascii=False)
    )
    manifest_payload = {
        k: v for k, v in payload.items() if k not in {"generated_at_utc", "manifest_sha256"}
    }
    payload["manifest_sha256"] = sha256_text(
        json.dumps(manifest_payload, sort_keys=True, ensure_ascii=False)
    )
    if manifest_path:
        write_json(manifest_path, payload)
    return payload


def build_change_report(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    prev_files = {f["path"]: f for f in (previous or {}).get("files", [])}
    cur_files = {f["path"]: f for f in current.get("files", [])}
    added = sorted(set(cur_files) - set(prev_files))
    removed = sorted(set(prev_files) - set(cur_files))
    changed = sorted(
        path
        for path in set(cur_files) & set(prev_files)
        if cur_files[path].get("sha256") != prev_files[path].get("sha256")
    )
    previous_content = (previous or {}).get("content_sha256") or (previous or {}).get(
        "manifest_sha256"
    )
    current_content = current.get("content_sha256") or current.get("manifest_sha256")
    return {
        "schema_version": "1.1",
        "generated_at_utc": utc_now_iso(),
        "previous_manifest_sha256": (previous or {}).get("manifest_sha256"),
        "current_manifest_sha256": current.get("manifest_sha256"),
        "previous_content_sha256": previous_content,
        "current_content_sha256": current_content,
        "added": added,
        "removed": removed,
        "changed": changed,
        "has_changes": bool(added or removed or changed or previous_content != current_content),
    }
