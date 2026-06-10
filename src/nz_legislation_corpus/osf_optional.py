from __future__ import annotations

from pathlib import Path

OSF_DEFAULT_SINGLE_FILE_LIMIT_BYTES = 5_000_000_000


def assert_osf_file_sizes(
    paths: list[Path], limit_bytes: int = OSF_DEFAULT_SINGLE_FILE_LIMIT_BYTES
) -> None:
    too_large = [path for path in paths if path.stat().st_size >= limit_bytes]
    if too_large:
        formatted = ", ".join(f"{p.name}={p.stat().st_size}" for p in too_large)
        raise ValueError(
            "OSF mirror refused because one or more files exceed the configured per-file limit. "
            f"Split the archive first. Files: {formatted}"
        )
