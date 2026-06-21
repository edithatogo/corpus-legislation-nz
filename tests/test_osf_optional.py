from __future__ import annotations

from pathlib import Path

import pytest

from nz_legislation_corpus.osf_optional import assert_osf_file_sizes


@pytest.mark.unit
def test_assert_osf_file_sizes_accepts_files_below_limit(tmp_path: Path) -> None:
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(b"abc")

    assert_osf_file_sizes([archive], limit_bytes=4)


@pytest.mark.unit
def test_assert_osf_file_sizes_rejects_files_at_limit(tmp_path: Path) -> None:
    archive = tmp_path / "archive.tar.gz"
    archive.write_bytes(b"abcd")

    with pytest.raises(ValueError, match="OSF mirror refused"):
        assert_osf_file_sizes([archive], limit_bytes=4)
