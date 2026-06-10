from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .utils import sha256_file, write_json

PACKAGE_VERSION = "0.1.0"
DATASET_ID = "corpus-nz-legislation"
LIVE_DATASET_URL = "https://huggingface.co/datasets/edithatogo/corpus-legislation-nz"
HISTORICAL_DATASET_URL = (
    "https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical"
)
GITHUB_URL = "https://github.com/edithatogo/corpus-legislation-nz"
ZENODO_URL = "https://zenodo.org/records/20592540"
ZENODO_DOI = "10.5281/zenodo.20592540"

PACKAGE_FILENAMES = {
    "croissant": "croissant.json",
    "ro_crate": "ro-crate-metadata.json",
    "frictionless": "datapackage.json",
    "dcat": "dcat.jsonld",
    "prov_o": "prov-o.jsonld",
}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _source_manifest(root: Path) -> dict[str, Any]:
    manifest = _read_json(root / "data" / "manifests" / "latest_manifest.json")
    if manifest:
        return {
            "path": "data/manifests/latest_manifest.json",
            "manifest_sha256": manifest.get("manifest_sha256"),
            "content_sha256": manifest.get("content_sha256"),
            "record_count": manifest.get("record_count"),
            "schema_version": manifest.get("schema_version"),
        }
    schema_path = root / "schemas" / "shared_nz_corpus_core.schema.json"
    return {
        "path": "schemas/shared_nz_corpus_core.schema.json",
        "manifest_sha256": sha256_file(schema_path),
        "content_sha256": sha256_file(schema_path),
        "record_count": None,
        "schema_version": "shared-nz-corpus-core",
    }


def _base_context(root: Path) -> dict[str, Any]:
    source_manifest = _source_manifest(root)
    shared_schema_path = root / "schemas" / "shared_nz_corpus_core.schema.json"
    record_schema_path = root / "schemas" / "legislation_record.schema.json"
    return {
        "dataset_id": DATASET_ID,
        "preferred_family_label": "corpus-nz-legislation",
        "current_public_label": "corpus-legislation-nz",
        "sibling_corpus": "corpus-nz-hansard",
        "name": "New Zealand Legislation Corpus",
        "description": (
            "API-first New Zealand legislation corpus pipeline. Coverage is not proven "
            "complete until reconciled against an authoritative inventory."
        ),
        "language": "en",
        "jurisdiction": "New Zealand",
        "country": "NZ",
        "coverage_status": "partial",
        "rights_note": (
            "Repository code is MIT licensed. Dataset publication does not relicense "
            "upstream legislation text, incorporated-by-reference material, third-party "
            "material, logos, emblems, or non-legislative linked content."
        ),
        "github_url": GITHUB_URL,
        "live_dataset_url": LIVE_DATASET_URL,
        "historical_dataset_url": HISTORICAL_DATASET_URL,
        "zenodo_url": ZENODO_URL,
        "zenodo_doi": ZENODO_DOI,
        "source_manifest": source_manifest,
        "shared_schema_path": "schemas/shared_nz_corpus_core.schema.json",
        "shared_schema_sha256": sha256_file(shared_schema_path),
        "record_schema_path": "schemas/legislation_record.schema.json",
        "record_schema_sha256": sha256_file(record_schema_path),
        "generated_at_utc": _now(),
        "package_version": PACKAGE_VERSION,
    }


def _croissant(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
        },
        "@type": "cr:Dataset",
        "@id": ctx["live_dataset_url"],
        "name": ctx["name"],
        "description": ctx["description"],
        "url": ctx["live_dataset_url"],
        "license": "https://www.legislation.govt.nz/about.aspx",
        "sameAs": [ctx["github_url"], ctx["zenodo_url"]],
        "keywords": ["New Zealand", "legislation", "law", "legal corpus"],
        "isAccessibleForFree": True,
        "distribution": [
            {
                "@type": "cr:FileSet",
                "@id": f"{ctx['live_dataset_url']}#parquet",
                "name": "Hugging Face Parquet files",
                "encodingFormat": "application/vnd.apache.parquet",
                "containedIn": ctx["live_dataset_url"],
                "includes": "parquet/**/*.parquet",
            }
        ],
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "@id": f"{ctx['live_dataset_url']}#records",
                "name": "Legislation records",
                "field": [
                    {"@type": "cr:Field", "name": "stable_id", "dataType": "sc:Text"},
                    {"@type": "cr:Field", "name": "title", "dataType": "sc:Text"},
                    {"@type": "cr:Field", "name": "text", "dataType": "sc:Text"},
                    {"@type": "cr:Field", "name": "text_sha256", "dataType": "sc:Text"},
                ],
            }
        ],
        "conformsTo": "https://mlcommons.org/croissant/1.0",
        "sourceManifest": ctx["source_manifest"],
        "rightsNote": ctx["rights_note"],
    }


def _ro_crate(ctx: dict[str, Any]) -> dict[str, Any]:
    dataset_id = "./"
    return {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": dataset_id},
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            },
            {
                "@id": dataset_id,
                "@type": "Dataset",
                "name": ctx["name"],
                "description": ctx["description"],
                "identifier": [ctx["live_dataset_url"], f"https://doi.org/{ctx['zenodo_doi']}"],
                "url": ctx["live_dataset_url"],
                "sameAs": [{"@id": ctx["github_url"]}, {"@id": ctx["zenodo_url"]}],
                "hasPart": [
                    {"@id": "parquet/"},
                    {"@id": "records.jsonl"},
                    {"@id": ctx["shared_schema_path"]},
                    {"@id": ctx["record_schema_path"]},
                ],
                "license": {"@id": "https://www.legislation.govt.nz/about.aspx"},
                "sdPublisher": {"@id": ctx["github_url"]},
                "dateModified": ctx["generated_at_utc"],
            },
            {
                "@id": ctx["shared_schema_path"],
                "@type": "CreativeWork",
                "name": "Shared NZ corpus core schema",
                "sha256": ctx["shared_schema_sha256"],
            },
            {
                "@id": ctx["record_schema_path"],
                "@type": "CreativeWork",
                "name": "NZ legislation record schema",
                "sha256": ctx["record_schema_sha256"],
            },
        ],
    }


def _frictionless(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile": "data-package",
        "name": DATASET_ID,
        "title": ctx["name"],
        "description": ctx["description"],
        "homepage": ctx["live_dataset_url"],
        "licenses": [
            {
                "name": "other",
                "title": "Source-content rights vary; see NOTICE.md and source terms",
                "path": "https://www.legislation.govt.nz/about.aspx",
            }
        ],
        "sources": [
            {"title": "GitHub repository", "path": ctx["github_url"]},
            {"title": "Hugging Face live dataset", "path": ctx["live_dataset_url"]},
            {"title": "Zenodo DOI snapshot", "path": ctx["zenodo_url"]},
        ],
        "resources": [
            {
                "name": "records",
                "path": "records.jsonl",
                "profile": "tabular-data-resource",
                "format": "jsonl",
                "schema": {"path": ctx["record_schema_path"]},
            },
            {
                "name": "parquet",
                "path": "parquet/**/*.parquet",
                "format": "parquet",
                "mediatype": "application/vnd.apache.parquet",
            },
        ],
        "custom": {
            "preferred_family_label": ctx["preferred_family_label"],
            "sibling_corpus": ctx["sibling_corpus"],
            "source_manifest": ctx["source_manifest"],
            "shared_schema": {
                "path": ctx["shared_schema_path"],
                "sha256": ctx["shared_schema_sha256"],
            },
            "coverage_status": ctx["coverage_status"],
            "rights_note": ctx["rights_note"],
        },
    }


def _dcat(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
        },
        "@id": ctx["live_dataset_url"],
        "@type": "dcat:Dataset",
        "dct:title": ctx["name"],
        "dct:description": ctx["description"],
        "dct:identifier": DATASET_ID,
        "dct:language": ctx["language"],
        "dct:spatial": ctx["jurisdiction"],
        "dct:publisher": {
            "@id": ctx["github_url"],
            "@type": "foaf:Agent",
            "foaf:name": "edithatogo",
        },
        "dct:relation": [{"@id": ctx["historical_dataset_url"]}, {"@id": ctx["zenodo_url"]}],
        "dct:conformsTo": {"@id": ctx["shared_schema_path"]},
        "dcat:keyword": ["New Zealand", "legislation", "legal corpus"],
        "dcat:distribution": [
            {
                "@type": "dcat:Distribution",
                "dct:title": "Live Hugging Face dataset",
                "dcat:accessURL": {"@id": ctx["live_dataset_url"]},
                "dct:format": "application/vnd.apache.parquet",
            },
            {
                "@type": "dcat:Distribution",
                "dct:title": "Zenodo DOI snapshot",
                "dcat:accessURL": {"@id": ctx["zenodo_url"]},
            },
        ],
        "sourceManifest": ctx["source_manifest"],
        "rightsNote": ctx["rights_note"],
    }


def _prov_o(ctx: dict[str, Any]) -> dict[str, Any]:
    generation = f"{ctx['github_url']}#metadata-packages-{ctx['package_version']}"
    return {
        "@context": {
            "prov": "http://www.w3.org/ns/prov#",
            "dct": "http://purl.org/dc/terms/",
        },
        "@graph": [
            {
                "@id": ctx["live_dataset_url"],
                "@type": "prov:Entity",
                "dct:title": ctx["name"],
                "prov:wasDerivedFrom": {"@id": ctx["source_manifest"]["path"]},
            },
            {
                "@id": ctx["source_manifest"]["path"],
                "@type": "prov:Entity",
                "dct:identifier": ctx["source_manifest"].get("manifest_sha256"),
            },
            {
                "@id": generation,
                "@type": "prov:Activity",
                "prov:startedAtTime": ctx["generated_at_utc"],
                "prov:endedAtTime": ctx["generated_at_utc"],
                "prov:used": [
                    {"@id": ctx["source_manifest"]["path"]},
                    {"@id": ctx["shared_schema_path"]},
                ],
                "prov:generated": [{"@id": name} for name in PACKAGE_FILENAMES.values()],
            },
            {
                "@id": ctx["github_url"],
                "@type": "prov:Agent",
                "dct:title": "corpus-legislation-nz GitHub repository",
            },
        ],
        "rightsNote": ctx["rights_note"],
    }


def _package_payloads(ctx: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "croissant": _croissant(ctx),
        "ro_crate": _ro_crate(ctx),
        "frictionless": _frictionless(ctx),
        "dcat": _dcat(ctx),
        "prov_o": _prov_o(ctx),
    }


def build_metadata_packages(root: Path, output_dir: Path) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ctx = _base_context(root)
    payloads = _package_payloads(ctx)

    files: list[dict[str, Any]] = []
    for package_id, payload in payloads.items():
        filename = PACKAGE_FILENAMES[package_id]
        path = output_dir / filename
        write_json(path, payload)
        files.append(
            {
                "package": package_id,
                "path": filename,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )

    validation = validate_metadata_packages(output_dir, root=root)
    manifest = {
        "schema_version": "1.0",
        "package_version": PACKAGE_VERSION,
        "generated_at_utc": ctx["generated_at_utc"],
        "source_manifest": ctx["source_manifest"],
        "shared_schema": {
            "path": ctx["shared_schema_path"],
            "sha256": ctx["shared_schema_sha256"],
        },
        "publication_surfaces": {
            "github": ctx["github_url"],
            "hugging_face_live": ctx["live_dataset_url"],
            "hugging_face_historical": ctx["historical_dataset_url"],
            "zenodo": ctx["zenodo_url"],
            "osf": None,
        },
        "files": files,
        "validation": validation,
        "coverage_status": ctx["coverage_status"],
        "rights_note": ctx["rights_note"],
    }
    manifest_path = output_dir / "metadata-package-manifest.json"
    write_json(manifest_path, manifest)
    checksums_path = output_dir / "SHA256SUMS.txt"
    checksum_lines = [f"{item['sha256']}  {item['path']}" for item in files]
    checksum_lines.append(f"{sha256_file(manifest_path)}  {manifest_path.name}")
    checksums_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return {
        "ok": validation["ok"],
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "checksums_path": str(checksums_path),
        "files": files,
        "validation": validation,
    }


def _require_keys(
    payload: dict[str, Any], keys: tuple[str, ...], errors: list[str], label: str
) -> None:
    for key in keys:
        if key not in payload:
            errors.append(f"{label} missing {key}")


def validate_metadata_packages(output_dir: Path, *, root: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    root = Path(root or Path.cwd())
    errors: list[str] = []
    package_results: dict[str, dict[str, Any]] = {}

    for package_id, filename in PACKAGE_FILENAMES.items():
        path = output_dir / filename
        if not path.exists():
            errors.append(f"{filename} is missing")
            package_results[package_id] = {"exists": False, "errors": [f"{filename} missing"]}
            continue
        package_errors: list[str] = []
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            errors.append(f"{filename} is not valid JSON: {exc}")
            package_results[package_id] = {"exists": True, "errors": [str(exc)]}
            continue
        _require_keys(
            payload, ("@context",), package_errors, filename
        ) if package_id != "frictionless" else None
        if package_id == "croissant":
            _require_keys(
                payload, ("@type", "name", "distribution", "recordSet"), package_errors, filename
            )
        elif package_id == "ro_crate":
            _require_keys(payload, ("@graph",), package_errors, filename)
        elif package_id == "frictionless":
            _require_keys(payload, ("profile", "name", "resources"), package_errors, filename)
        elif package_id == "dcat":
            _require_keys(payload, ("@type", "dcat:distribution"), package_errors, filename)
        elif package_id == "prov_o":
            _require_keys(payload, ("@graph",), package_errors, filename)
        package_results[package_id] = {
            "exists": True,
            "sha256": sha256_file(path),
            "errors": package_errors,
        }
        errors.extend(package_errors)

    schema_path = root / "schemas" / "shared_nz_corpus_core.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        errors.append(f"shared core schema validation failed: {exc}")

    return {
        "ok": not errors,
        "packages": package_results,
        "errors": errors,
        "validation_commands": [
            "uv run nzlc metadata-packages --output-dir generated/metadata-packages",
            "uv run nzlc validate-metadata-packages --metadata-dir generated/metadata-packages",
        ],
    }
