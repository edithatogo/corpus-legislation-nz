from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
SCHEMA_VERSION_RE = re.compile(r"^\d+\.\d+$")
ZENODO_DOI = "10.5281/zenodo.20592540"
PARTIAL_RELEASE_TAG = "v0.1.0-partial.20260609"

DOI_SURFACES = (
    "CITATION.cff",
    "DATASET_CARD.md",
    "README.md",
    "docs/public_launch_decision.md",
    "docs/public_launch_release_note.md",
    "docs/public_surface_evidence_ledger.md",
)

RELEASE_TAG_SURFACES = (
    "docs/public_launch_decision.md",
    "docs/public_launch_release_note.md",
    "docs/public_surface_evidence_ledger.md",
    "conductor/tracks.md",
)

REQUIRED_GOVERNANCE_SNIPPETS = (
    "corpus-nz-legislation",
    "corpus-nz-hansard",
    "Code/package version",
    "Dataset citation version",
    "Record schema version",
    "Hugging Face revision",
    "Zenodo DOI snapshot",
    "Manifest hash",
    "Release Please",
    "deferred",
    "validation gates",
    "zenodraft",
)


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def _json(path: str) -> dict[str, Any]:
    return json.loads(_text(path))


def _pyproject_version() -> str:
    payload = tomllib.loads(_text("pyproject.toml"))
    return str(payload["project"]["version"])


def _quoted_assignment(path: str, name: str) -> str:
    match = re.search(rf'^{re.escape(name)}\s*=\s*"([^"]+)"\s*$', _text(path), re.MULTILINE)
    if not match:
        raise ValueError(f"{path} does not define {name}")
    return match.group(1)


def _cff_field(name: str) -> str:
    match = re.search(
        rf"^{re.escape(name)}:\s*\"?([^\"\n]+)\"?\s*$", _text("CITATION.cff"), re.MULTILINE
    )
    if not match:
        raise ValueError(f"CITATION.cff does not define {name}")
    return match.group(1)


def _record_schema_const() -> str:
    schema = _json("schemas/legislation_record.schema.json")
    return str(schema["properties"]["record_schema_version"]["const"])


def _manifest_failures() -> list[str]:
    manifest_path = ROOT / "data" / "manifests" / "latest_manifest.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    failures: list[str] = []
    for key in ("manifest_sha256", "content_sha256"):
        value = manifest.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
            failures.append(f"{manifest_path} has missing or invalid {key}")
    if "schema_version" not in manifest and "record_schema_version" not in manifest:
        failures.append(f"{manifest_path} does not record a schema version")
    return failures


def check_version_consistency() -> list[str]:
    failures: list[str] = []

    package_version = _pyproject_version()
    init_version = _quoted_assignment("src/nz_legislation_corpus/__init__.py", "__version__")
    if package_version != init_version:
        failures.append(
            "Package version mismatch: pyproject.toml "
            f"{package_version} != __init__.py {init_version}"
        )
    if not SEMVER_RE.fullmatch(package_version):
        failures.append(f"Package version is not SemVer-like: {package_version}")

    citation_version = _cff_field("version")
    if not SEMVER_RE.fullmatch(citation_version):
        failures.append(f"CITATION.cff version is not SemVer-like: {citation_version}")

    metadata_package_version = _quoted_assignment(
        "src/nz_legislation_corpus/metadata_packages.py", "PACKAGE_VERSION"
    )
    if not SEMVER_RE.fullmatch(metadata_package_version):
        failures.append(f"Metadata package version is not SemVer-like: {metadata_package_version}")

    record_schema_python = _quoted_assignment(
        "src/nz_legislation_corpus/schema.py", "RECORD_SCHEMA_VERSION"
    )
    record_schema_json = _record_schema_const()
    if record_schema_python != record_schema_json:
        failures.append(
            "Record schema version mismatch: schema.py "
            f"{record_schema_python} != JSON Schema {record_schema_json}"
        )
    if not SCHEMA_VERSION_RE.fullmatch(record_schema_python):
        failures.append(f"Record schema version is not MAJOR.MINOR: {record_schema_python}")

    if _cff_field("doi") != ZENODO_DOI:
        failures.append("CITATION.cff DOI does not match the approved Zenodo DOI")

    for surface in DOI_SURFACES:
        if ZENODO_DOI not in _text(surface):
            failures.append(f"{surface} does not record Zenodo DOI {ZENODO_DOI}")

    for surface in RELEASE_TAG_SURFACES:
        if PARTIAL_RELEASE_TAG not in _text(surface):
            failures.append(f"{surface} does not record release tag {PARTIAL_RELEASE_TAG}")

    governance_doc = _text("docs/versioning_release_automation.md")
    for snippet in REQUIRED_GOVERNANCE_SNIPPETS:
        if snippet not in governance_doc:
            failures.append(
                f"docs/versioning_release_automation.md is missing required text: {snippet}"
            )

    failures.extend(_manifest_failures())
    return failures


def main() -> int:
    failures = check_version_consistency()
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Version and release consistency checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
