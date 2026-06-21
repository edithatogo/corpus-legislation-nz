"""Validate the OSF optional mirror policy document contract."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "osf-optional-mirror-policy.md"
MODULE_PATH = ROOT / "src" / "nz_legislation_corpus" / "osf_optional.py"
TRACK_SPEC_PATH = (
    ROOT
    / "conductor"
    / "tracks"
    / "track_35_multi_git_and_multi_archive_mirroring_setup"
    / "spec.md"
)

REQUIRED_DOC_SNIPPETS = (
    "Inactive",
    "Hugging Face",
    "Zenodo",
    "5 GB",
    "osf_optional.py",
    "assert_osf_file_sizes",
    "Activation criteria",
    "Track 07",
    "Track 08",
    "GitHub",
    "convenience mirror",
    "per-file upload limit",
)

REQUIRED_TRACK_SNIPPETS = (
    "docs/osf-optional-mirror-policy.md",
    "Multi-Git Mirroring",
    "Multi-Archive",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def find_failures() -> list[str]:
    found: list[str] = []

    if not DOC_PATH.exists():
        found.append("OSF optional mirror policy doc is missing.")
        return found

    if not MODULE_PATH.exists():
        found.append("osf_optional.py module is missing.")

    docs = _read_text(DOC_PATH)

    if "**Inactive**" not in docs:
        found.append("Policy doc must state **Inactive** status.")

    for snippet in REQUIRED_DOC_SNIPPETS:
        if snippet not in docs:
            found.append(f"Policy doc is missing required snippet: {snippet}")

    track_spec = _read_text(TRACK_SPEC_PATH) if TRACK_SPEC_PATH.exists() else ""
    if not track_spec:
        found.append("Track 35 spec.md is missing.")
    else:
        for snippet in REQUIRED_TRACK_SNIPPETS:
            if snippet not in track_spec:
                found.append(f"Track 35 spec.md is missing required snippet: {snippet}")

    return found


def main() -> int:
    found = find_failures()
    if found:
        for failure in found:
            print(f"OSF-POLICY: {failure}")
        return 1
    print("OSF optional mirror policy contract is consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
