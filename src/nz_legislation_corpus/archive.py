from __future__ import annotations

import tarfile
from pathlib import Path

from .manifest import build_manifest
from .utils import sha256_file, write_json

_EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "cache", ".cache"}
_EXCLUDED_NAMES = {".DS_Store"}


def _tar_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    parts = set(Path(tarinfo.name).parts)
    if parts & _EXCLUDED_PARTS:
        return None
    if Path(tarinfo.name).name in _EXCLUDED_NAMES:
        return None
    return tarinfo


def build_archive(input_dir: Path, output_dir: Path, *, year: str, prefer_zstd: bool = True) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = f"corpus-legislation-nz-{year}.tar"
    archive_path = output_dir / (base + ".zst")
    compression = "zstd"

    if prefer_zstd:
        try:
            import zstandard as zstd

            cctx = zstd.ZstdCompressor(level=10, threads=0)
            with (
                archive_path.open("wb") as raw_out,
                cctx.stream_writer(raw_out) as compressor,
                tarfile.open(fileobj=compressor, mode="w|") as tar,
            ):
                tar.add(input_dir, arcname="corpus-legislation-nz", filter=_tar_filter)
        except Exception:  # noqa: BLE001
            archive_path = output_dir / (base + ".gz")
            compression = "gzip"
            with tarfile.open(archive_path, mode="w:gz") as tar:
                tar.add(input_dir, arcname="corpus-legislation-nz", filter=_tar_filter)
    else:
        archive_path = output_dir / (base + ".gz")
        compression = "gzip"
        with tarfile.open(archive_path, mode="w:gz") as tar:
            tar.add(input_dir, arcname="corpus-legislation-nz", filter=_tar_filter)

    manifest_path = output_dir / f"corpus-legislation-nz-{year}.manifest.json"
    manifest = build_manifest(input_dir)
    manifest["archive_file"] = archive_path.name
    manifest["archive_sha256"] = sha256_file(archive_path)
    manifest["archive_compression"] = compression
    write_json(manifest_path, manifest)

    checksums_path = output_dir / f"corpus-legislation-nz-{year}.SHA256SUMS.txt"
    lines = []
    for path in [archive_path, manifest_path]:
        lines.append(f"{sha256_file(path)}  {path.name}")
    checksums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "archive_path": str(archive_path),
        "manifest_path": str(manifest_path),
        "checksums_path": str(checksums_path),
        "compression": compression,
    }
