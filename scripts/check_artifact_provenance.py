from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def failures() -> list[str]:
    found: list[str] = []
    schema_path = ROOT / "schemas" / "release_evidence.schema.json"
    schema = _read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        found.append(f"{schema_path} is not a valid JSON Schema: {exc}")

    docs = (ROOT / "docs" / "artifact_provenance_attestations.md").read_text(encoding="utf-8-sig")
    required_snippets = [
        "corpus-nz-legislation",
        "corpus-nz-hansard",
        "GitHub artifact attestation",
        "SLSA-style provenance",
        "SHA256SUMS",
        "Zenodo",
        "Hugging Face",
        "validation gates",
        "zenodraft",
    ]
    for snippet in required_snippets:
        if snippet not in docs:
            found.append(f"artifact provenance policy missing required text: {snippet}")

    archive_workflow = (ROOT / ".github" / "workflows" / "annual_zenodo_archive.yml").read_text(
        encoding="utf-8-sig"
    )
    for snippet in [
        "attestations: write",
        "id-token: write",
        "actions/attest",
        ".release-evidence.json",
    ]:
        if snippet not in archive_workflow:
            found.append(f"annual Zenodo workflow missing required attestation text: {snippet}")

    for path in sorted((ROOT / "dist" / "archive").glob("*.release-evidence.json")):
        payload = _read_json(path)
        errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=str)
        found.extend(f"{path}: {error}" for error in errors)

    return found


def main() -> int:
    found = failures()
    if found:
        for failure in found:
            print(f"ERROR: {failure}")
        return 1
    print("Artifact provenance policy and evidence checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
