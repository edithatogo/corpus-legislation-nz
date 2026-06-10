from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .utils import sha256_file, utc_now_iso, write_json


def _env(name: str) -> str:
    return os.getenv(name, "")


def build_release_evidence(
    *,
    artifact_class: str,
    output_path: Path,
    subjects: list[Path],
    manifest: dict[str, Any],
    coverage_statement: str,
    publication_target: str,
    zenodo_doi: str | None = None,
    zenodo_concept_doi: str | None = None,
    huggingface_revision: str | None = None,
) -> dict[str, Any]:
    subject_payloads = [
        {
            "path": path.name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in subjects
    ]
    evidence = {
        "schema_version": "1.0",
        "artifact_class": artifact_class,
        "generated_at_utc": utc_now_iso(),
        "corpus_family_label": "corpus-nz-legislation",
        "sibling_corpus": "corpus-nz-hansard",
        "publication_target": publication_target,
        "coverage_statement": coverage_statement,
        "source_repository": _env("GITHUB_REPOSITORY"),
        "source_commit_sha": _env("GITHUB_SHA") or manifest.get("pipeline_version") or "local-dev",
        "workflow": {
            "name": _env("GITHUB_WORKFLOW"),
            "run_id": _env("GITHUB_RUN_ID"),
            "run_attempt": _env("GITHUB_RUN_ATTEMPT"),
            "ref": _env("GITHUB_REF"),
            "event_name": _env("GITHUB_EVENT_NAME"),
        },
        "dataset": {
            "huggingface_repo_id": _env("HF_REPO_ID") or manifest.get("hf_repo_id") or "",
            "huggingface_revision": huggingface_revision or _env("HF_REVISION") or "",
            "zenodo_doi": zenodo_doi or _env("ZENODO_DOI") or "",
            "zenodo_concept_doi": zenodo_concept_doi or _env("ZENODO_CONCEPT_DOI") or "",
        },
        "manifest": {
            "manifest_sha256": manifest.get("manifest_sha256"),
            "content_sha256": manifest.get("content_sha256"),
            "schema_version": manifest.get("schema_version"),
            "record_schema_version": manifest.get("record_schema_version"),
            "record_count": manifest.get("record_count"),
        },
        "subjects": subject_payloads,
        "attestation_policy": {
            "github_artifact_attestation": "required_for_github_actions_archive_builds",
            "signed_checksums": "sha256sums_required; cryptographic signing deferred",
            "slsa_style_provenance": "release_evidence_json_plus_github_artifact_attestation",
        },
    }
    write_json(output_path, evidence)
    return evidence
