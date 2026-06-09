from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from .archive import build_archive
from .config import Settings, require
from .discovery import build_work_id_inventory
from .manifest import build_change_report, build_manifest
from .normalize import normalize_version_record
from .nz_api import NZLegislationClient
from .parquet_writer import write_partitioned_parquet
from .schema import RECORD_SCHEMA_VERSION
from .types import SyncStats
from .utils import (
    read_json,
    read_jsonl,
    slug_for_path,
    write_json,
    write_jsonl,
    write_jsonl_if_changed,
)
from .validate import validate_records
from .zenodo import upload_archive_to_zenodo

app = typer.Typer(help="NZ legislation corpus pipeline CLI")
console = Console()
logging.basicConfig(level=os.getenv("NZLC_LOG_LEVEL", "INFO"), format="%(levelname)s %(message)s")


def _load_seed_work_ids(path: Path | None) -> list[str]:
    if not path or not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _split_option(value: str | None, default: list[str]) -> list[str]:
    if value is None or not value.strip():
        return default
    return [part.strip() for part in value.split(",") if part.strip()]


def _optional_filter(value: str | None, default: str | None) -> str | None:
    candidate = default if value is None else value
    if candidate is None:
        return None
    candidate = candidate.strip()
    if not candidate or candidate.lower() in {"none", "null", "-"}:
        return None
    return candidate


def _safe_write_raw(raw_dir: Path, stable_id: str, content: bytes, suffix: str = ".xml") -> Path:
    path = raw_dir / f"{slug_for_path(stable_id)}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != content:
        path.write_bytes(content)
    return path


@app.command()
def doctor(
    network: Annotated[
        bool, typer.Option(help="Check remote services as well as local config.")
    ] = False,
) -> None:
    """Check local configuration without doing destructive work."""
    settings = Settings.from_env()
    checks = {
        "NZ_LEGISLATION_API_KEY": bool(settings.nz_api_key),
        "HF_REPO_ID": bool(settings.hf_repo_id),
        "HF_TOKEN": bool(settings.hf_token),
        "ZENODO_TOKEN": bool(settings.zenodo_token),
        "ARCHIVE_CREATORS_JSON": bool(settings.archive_creators),
        "output_dir": str(settings.output_dir),
    }
    for name, ok in checks.items():
        console.print(f"{'[OK]' if ok else '[WARN]'} {name}: {ok}")
    if network and settings.nz_api_key:
        client = NZLegislationClient(settings)
        # Smallest non-destructive call. Search term chosen as common and likely to succeed.
        payload = client.search_works(search_term="Act", search_field="title", page=1, per_page=1)
        console.print(f"[OK] NZ API reachable; sample total={payload.get('total')}")

    if network and settings.hf_token and settings.hf_repo_id:
        from huggingface_hub import HfApi

        info = HfApi(token=settings.hf_token).repo_info(
            repo_id=settings.hf_repo_id,
            repo_type="dataset",
        )
        console.print(f"[OK] Hugging Face dataset reachable; id={info.id}")

    if network and settings.zenodo_token:
        import requests

        url = settings.zenodo_api_url.rstrip("/") + "/deposit/depositions"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {settings.zenodo_token}"},
            params={"size": 1},
            timeout=settings.request_timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Zenodo API check failed: HTTP {response.status_code} {response.text[:200]}"
            )
        console.print(f"[OK] Zenodo API reachable at {settings.zenodo_api_url}")


@app.command()
def sync(
    seed_work_ids: Annotated[
        Path | None, typer.Option(help="Optional file containing work IDs, one per line.")
    ] = None,
    latest_only: Annotated[
        bool, typer.Option(help="Only pull latest matching version for discovered works.")
    ] = False,
    max_works: Annotated[
        int | None, typer.Option(help="Limit work discovery for smoke tests.")
    ] = None,
    allow_no_search_terms: Annotated[
        bool, typer.Option(help="Allow no search terms if seed work IDs are supplied.")
    ] = False,
    replace: Annotated[
        bool, typer.Option(help="Replace existing records instead of merging into records.jsonl.")
    ] = False,
    embeddings: Annotated[
        bool,
        typer.Option(
            help="Generate dense, sparse, and ColBERT embeddings for each record using BAAI/bge-m3."
        ),
    ] = False,
) -> None:
    """Fetch legislation metadata/content, normalize records, and write JSONL + Parquet."""
    settings = Settings.from_env()
    seed_ids = _load_seed_work_ids(seed_work_ids)
    if not settings.search_terms and not seed_ids and not allow_no_search_terms:
        raise typer.BadParameter(
            "Set NZLC_SEARCH_TERMS or pass --seed-work-ids for deterministic discovery."
        )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.raw_xml_dir.mkdir(parents=True, exist_ok=True)
    settings.manifests_dir.mkdir(parents=True, exist_ok=True)
    settings.state_dir.mkdir(parents=True, exist_ok=True)

    state = read_json(settings.sync_state_path, default={"versions": {}})
    existing_rows = read_jsonl(settings.records_jsonl_path)
    known_versions: dict[str, str] = dict(state.get("versions", {}))
    if not known_versions:
        known_versions = {
            str(r.get("stable_id")): str(r.get("source_hash"))
            for r in existing_rows
            if r.get("stable_id") and r.get("source_hash")
        }
    client = NZLegislationClient(settings)
    stats = SyncStats()
    existing_records = (
        {} if replace else {str(r.get("stable_id")): r for r in existing_rows if r.get("stable_id")}
    )
    records: list[dict[str, Any]] = []
    seen_work_ids_for_stats: set[str] = set()

    for version_stub in client.discover_versions(
        search_terms=settings.search_terms,
        search_field=settings.search_field,
        seed_work_ids=seed_ids,
        latest_only=latest_only,
        max_works=max_works,
    ):
        stats.versions_checked += 1
        version_id = str(version_stub.get("version_id") or "")
        work_id_for_stats = str(version_stub.get("work_id") or "")
        if work_id_for_stats and work_id_for_stats not in seen_work_ids_for_stats:
            seen_work_ids_for_stats.add(work_id_for_stats)
            stats.works_checked += 1
        try:
            version = (
                client.get_version(version_id)
                if version_id and "administering_agencies" not in version_stub
                else version_stub
            )
            raw_url = client.format_url(version, "xml") or client.format_url(version, "html")
            raw_content = b""
            raw_type = None
            if raw_url:
                raw_content = client.download_url(raw_url)
                raw_type = (
                    "application/xml"
                    if raw_url.lower().endswith(".xml/") or ".xml" in raw_url.lower()
                    else "text/html"
                )
            record = normalize_version_record(
                version,
                raw_content=raw_content,
                raw_content_url=raw_url,
                raw_content_type=raw_type,
                pipeline_version=settings.pipeline_version,
            )
            if raw_content:
                suffix = ".xml" if raw_type == "application/xml" else ".html"
                raw_path = _safe_write_raw(
                    settings.raw_xml_dir, record["stable_id"], raw_content, suffix=suffix
                )
                record["raw_content_path"] = raw_path.relative_to(settings.output_dir).as_posix()
            previous_hash = known_versions.get(record["stable_id"])
            prior_record = existing_records.get(record["stable_id"])

            has_changed = (previous_hash is None) or (previous_hash != record["source_hash"])
            if embeddings and has_changed and record.get("text"):
                try:
                    from .embeddings import compute_all_three_embeddings

                    emb = compute_all_three_embeddings(record["text"])
                    record["embedding_dense"] = emb["dense"]
                    record["embedding_sparse"] = json.dumps(emb["lexical_weights"])
                    record["embedding_colbert"] = emb["colbert_multivector"]
                except Exception as emb_exc:
                    stats.warnings.append(
                        f"Failed to generate embeddings for {record['stable_id']}: {emb_exc}"
                    )

            if previous_hash is None:
                stats.records_added += 1
                records.append(record)
                existing_records[record["stable_id"]] = record
            elif previous_hash != record["source_hash"]:
                stats.records_changed += 1
                records.append(record)
                existing_records[record["stable_id"]] = record
            else:
                stats.records_unchanged += 1
                # Preserve the already published record exactly. Fresh scrape timestamps are
                # diagnostics, not corpus content, and rewriting them would force needless uploads.
                if prior_record:
                    records.append(prior_record)
                else:
                    records.append(record)
                    existing_records[record["stable_id"]] = record
            known_versions[record["stable_id"]] = record["source_hash"]
        except Exception as exc:  # noqa: BLE001
            stats.records_failed += 1
            stats.warnings.append(f"version {version_id or '<unknown>'} failed: {exc}")

    if not records:
        console.print(
            "No newly fetched records. Discovery may need seed work IDs or broader NZLC_SEARCH_TERMS."
        )
    merged_records = sorted(existing_records.values(), key=lambda r: str(r.get("stable_id", "")))
    records_changed_on_disk = write_jsonl_if_changed(settings.records_jsonl_path, merged_records)
    parquet_missing = not settings.parquet_dir.exists() or not any(
        settings.parquet_dir.rglob("*.parquet")
    )
    if merged_records and (records_changed_on_disk or parquet_missing):
        written = write_partitioned_parquet(merged_records, settings.parquet_dir)
    else:
        written = []
    stats.parquet_files_written = len(written)

    write_json(
        settings.sync_state_path,
        {
            "versions": known_versions,
            "last_stats": stats.as_dict(),
            "records_changed_on_disk": records_changed_on_disk,
        },
    )
    console.print_json(data=stats.as_dict())


@app.command("discover-work-ids")
def discover_work_ids_cmd(
    output_path: Annotated[
        Path, typer.Option(help="Write discovered work IDs, one per line.")
    ] = Path("seeds/discovered_work_ids.txt"),
    provenance_path: Annotated[
        Path,
        typer.Option(help="Write discovery provenance JSON."),
    ] = Path("seeds/discovered_work_ids.provenance.json"),
    search_terms: Annotated[
        str | None,
        typer.Option(help="Comma-separated search terms. Defaults to NZLC_SEARCH_TERMS."),
    ] = None,
    legislation_types: Annotated[
        str | None,
        typer.Option(help="Comma-separated legislation types. Defaults to NZLC_LEGISLATION_TYPES."),
    ] = None,
    legislation_status: Annotated[
        str | None,
        typer.Option(
            help=(
                "Legislation status filter, e.g. current. Use none/null/- to omit. "
                "Defaults to NZLC_LEGISLATION_STATUS."
            )
        ),
    ] = None,
    max_pages: Annotated[
        int | None, typer.Option(help="Optional page limit per search/type query.")
    ] = None,
    max_works: Annotated[
        int | None, typer.Option(help="Optional total discovered-work limit for pilots.")
    ] = None,
) -> None:
    """Discover work IDs for deterministic seed-based bootstraps."""
    settings = Settings.from_env()
    terms = _split_option(search_terms, settings.search_terms)
    if not terms:
        raise typer.BadParameter("Set NZLC_SEARCH_TERMS or pass --search-terms.")
    types = _split_option(legislation_types, settings.legislation_types)
    status = _optional_filter(legislation_status, settings.legislation_status)
    client = NZLegislationClient(settings)
    inventory = build_work_id_inventory(
        client,
        search_terms=terms,
        search_field=settings.search_field,
        legislation_types=types,
        legislation_status=status,
        sort_by=settings.search_sort_by,
        publisher=settings.publisher,
        max_pages=max_pages,
        max_works=max_works,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(inventory["work_ids"]) + ("\n" if inventory["work_ids"] else ""), encoding="utf-8"
    )
    write_json(provenance_path, inventory)
    console.print_json(
        data={
            "work_id_count": inventory["record_count"],
            "output_path": str(output_path),
            "provenance_path": str(provenance_path),
            "coverage_warning": inventory["coverage_warning"],
        }
    )


@app.command("validate")
def validate_cmd(
    records_path: Annotated[
        Path | None, typer.Option(help="Defaults to $NZLC_OUTPUT_DIR/records.jsonl")
    ] = None,
    schema_path: Annotated[Path, typer.Option(help="JSON Schema path")] = Path(
        "schemas/legislation_record.schema.json"
    ),
    allow_empty_text: Annotated[
        bool, typer.Option(help="Allow empty text for metadata-only tests.")
    ] = False,
) -> None:
    settings = Settings.from_env()
    path = records_path or settings.records_jsonl_path
    report = validate_records(
        path,
        schema_path=schema_path if schema_path.exists() else None,
        report_path=settings.manifests_dir / "validation_report.json",
        allow_empty_text=allow_empty_text,
    )
    console.print_json(data=report)
    if not report["ok"]:
        raise typer.Exit(code=2)


@app.command("manifest")
def manifest_cmd() -> None:
    settings = Settings.from_env()
    previous_path = settings.manifests_dir / "latest_manifest.json"
    previous = read_json(previous_path, default=None)
    current = build_manifest(settings.output_dir, manifest_path=previous_path)
    changes = build_change_report(previous, current)
    write_json(settings.manifests_dir / "latest_changes.json", changes)
    console.print_json(data={"manifest_sha256": current["manifest_sha256"], "changes": changes})


@app.command("hf-upload")
def hf_upload_cmd(
    force: Annotated[
        bool, typer.Option(help="Upload even if remote manifest hash matches.")
    ] = False,
    private: Annotated[
        bool, typer.Option(help="Create dataset repo as private if missing.")
    ] = False,
) -> None:
    from .hf_sync import create_dataset_repo_if_needed, remote_manifest, upload_large_folder

    settings = Settings.from_env()
    repo_id = require(settings.hf_repo_id, "HF_REPO_ID")
    token = require(settings.hf_token, "HF_TOKEN")
    validation = validate_records(
        settings.records_jsonl_path,
        schema_path=Path("schemas/legislation_record.schema.json"),
        report_path=settings.manifests_dir / "validation_report.json",
    )
    if not validation["ok"]:
        raise RuntimeError(
            "Blocking validation failures prevent Hugging Face upload; "
            f"see {settings.manifests_dir / 'validation_report.json'}"
        )
    create_dataset_repo_if_needed(repo_id, token=token, private=private)
    local_manifest = read_json(settings.manifests_dir / "latest_manifest.json", default=None)
    if not local_manifest:
        local_manifest = build_manifest(
            settings.output_dir, manifest_path=settings.manifests_dir / "latest_manifest.json"
        )
    remote = remote_manifest(repo_id, token=token, revision=settings.hf_revision)
    local_content = local_manifest.get("content_sha256") or local_manifest.get("manifest_sha256")
    remote_content = (remote or {}).get("content_sha256") or (remote or {}).get("manifest_sha256")
    if not force and remote and remote_content == local_content:
        console.print(
            "No corpus content changes relative to remote manifest; skipping Hugging Face upload."
        )
        return
    url = upload_large_folder(
        repo_id, settings.output_dir, token=token, revision=settings.hf_revision
    )
    console.print(url)


@app.command("archive")
def archive_cmd(
    year: Annotated[str, typer.Option(help="Archive year, e.g. 2026.")] = "2026",
    output_dir: Annotated[Path, typer.Option(help="Archive output directory.")] = Path(
        "dist/archive"
    ),
) -> None:
    settings = Settings.from_env()
    result = build_archive(settings.output_dir, output_dir, year=year)
    console.print_json(data=result)


@app.command("zenodo-upload")
def zenodo_upload_cmd(
    year: Annotated[str, typer.Option(help="Archive year.")] = "2026",
    archive_dir: Annotated[Path, typer.Option(help="Archive directory.")] = Path("dist/archive"),
    publish: Annotated[
        bool, typer.Option(help="Publish the Zenodo draft. Default false for safety.")
    ] = False,
) -> None:
    settings = Settings.from_env()
    token = require(settings.zenodo_token, "ZENODO_TOKEN")
    creators = settings.archive_creators
    if not creators:
        raise RuntimeError("ARCHIVE_CREATORS_JSON is required for Zenodo metadata")
    files = [
        archive_dir / f"nz-legislation-corpus-{year}.tar.zst",
        archive_dir / f"nz-legislation-corpus-{year}.tar.gz",
        archive_dir / f"nz-legislation-corpus-{year}.manifest.json",
        archive_dir / f"nz-legislation-corpus-{year}.SHA256SUMS.txt",
    ]
    files = [path for path in files if path.exists()]
    if not files:
        raise RuntimeError(f"No archive files found in {archive_dir}; run nzlc archive first")
    hf_related = []
    if settings.hf_repo_id:
        hf_related.append(
            {
                "identifier": f"https://huggingface.co/datasets/{settings.hf_repo_id}",
                "relation": "isSupplementTo",
                "resource_type": "dataset",
            }
        )
    result = upload_archive_to_zenodo(
        api_url=settings.zenodo_api_url,
        token=token,
        files=files,
        title=f"{settings.archive_title}: {year} annual snapshot",
        creators=creators,
        description=(
            "Annual, version-locked snapshot of the New Zealand legislation corpus. "
            "The live continuously updated corpus is maintained on Hugging Face Datasets."
        ),
        version=str(year),
        license_id=settings.archive_license,
        deposition_id=settings.zenodo_deposition_id,
        publish=publish or settings.archive_publish_default,
        related_identifiers=hf_related,
    )
    safe = {
        "draft_id": result["draft"].get("id"),
        "draft_html": result["draft"].get("links", {}).get("html"),
        "published": bool(result.get("published")),
        "uploaded_files": [Path(str(f)).name for f in files],
    }
    console.print_json(data=safe)


@app.command("smoke-fixture")
def smoke_fixture(output_dir: Annotated[Path, typer.Option()] = Path("data")) -> None:
    """Create a tiny fixture corpus without network access."""
    fixture = Path("tests/fixtures/sample_legislation.xml")
    if not fixture.exists():
        raise RuntimeError("Fixture missing")
    os.environ["NZLC_OUTPUT_DIR"] = str(output_dir)
    settings = Settings.from_env()
    xml_bytes = fixture.read_bytes()
    version = {
        "title": "Sample Act 2026",
        "version_id": "sample-act-2026/latest",
        "work_id": "sample-act-2026",
        "legislation_status": "current",
        "legislation_type": "act",
        "administering_agencies": ["Example Agency"],
        "formats": [{"type": "xml", "url": "https://example.invalid/sample.xml"}],
        "is_latest_version": True,
    }
    record = normalize_version_record(
        version,
        raw_content=xml_bytes,
        raw_content_url="https://example.invalid/sample.xml",
        raw_content_type="application/xml",
    )
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.raw_xml_dir.mkdir(parents=True, exist_ok=True)
    _safe_write_raw(settings.raw_xml_dir, record["stable_id"], xml_bytes, ".xml")
    write_jsonl(settings.records_jsonl_path, [record])
    write_partitioned_parquet([record], settings.parquet_dir)
    build_manifest(
        settings.output_dir, manifest_path=settings.manifests_dir / "latest_manifest.json"
    )
    console.print(f"Wrote smoke fixture corpus to {settings.output_dir}")


@app.command("coverage-report")
def coverage_report_cmd() -> None:
    """Summarize corpus coverage and red-team risk indicators."""
    settings = Settings.from_env()
    records = read_jsonl(settings.records_jsonl_path)
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_year: dict[str, int] = {}
    missing_text = 0
    missing_xml = 0
    ephemeral_ids = 0
    for record in records:
        by_type[str(record.get("legislation_type") or "unknown")] = (
            by_type.get(str(record.get("legislation_type") or "unknown"), 0) + 1
        )
        by_status[str(record.get("legislation_status") or "unknown")] = (
            by_status.get(str(record.get("legislation_status") or "unknown"), 0) + 1
        )
        by_year[str(record.get("year") or "unknown")] = (
            by_year.get(str(record.get("year") or "unknown"), 0) + 1
        )
        if not str(record.get("text") or "").strip():
            missing_text += 1
        if not str(record.get("xml_url") or "").strip():
            missing_xml += 1
        if record.get("id_is_ephemeral"):
            ephemeral_ids += 1
    report = {
        "schema_version": "1.0",
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "record_count": len(records),
        "by_type": dict(sorted(by_type.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_year": dict(sorted(by_year.items())),
        "risk_indicators": {
            "missing_text_records": missing_text,
            "missing_xml_url_records": missing_xml,
            "ephemeral_identifier_records": ephemeral_ids,
        },
        "recommendation": "Use a seed work-id list or official bulk source before claiming corpus completeness."
        if records
        else "No records found.",
    }
    write_json(settings.manifests_dir / "coverage_report.json", report)
    history_path = settings.manifests_dir / "coverage_history.jsonl"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report, sort_keys=True, ensure_ascii=False) + "\n")
    console.print_json(data=report)


if __name__ == "__main__":
    app()
