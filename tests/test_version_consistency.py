from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_version_consistency import (  # noqa: E402
    PARTIAL_RELEASE_TAG,
    SEMVER_RE,
    ZENODO_DOI,
    check_version_consistency,
)


def test_version_consistency_check_passes() -> None:
    assert check_version_consistency() == []


def test_release_identifiers_are_well_formed() -> None:
    assert SEMVER_RE.fullmatch("0.5.0")
    assert re.fullmatch(r"v\d+\.\d+\.\d+-partial\.\d{8}", PARTIAL_RELEASE_TAG)
    assert re.fullmatch(r"10\.\d{4,9}/zenodo\.\d+", ZENODO_DOI)
