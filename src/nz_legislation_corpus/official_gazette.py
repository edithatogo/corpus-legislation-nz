"""Official New Zealand Gazette archive helpers."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from .archive import build_archive
from .artifact_provenance import build_release_evidence
from .utils import read_jsonl, sha256_file, sha256_text, utc_now_iso, write_json

OFFICIAL_GAZETTE_SOURCE_ID = "official_gazette"
OFFICIAL_GAZETTE_SOURCE_NAME = "NZ Gazette official website"
OFFICIAL_GAZETTE_SOURCE_TIER = "official"
OFFICIAL_GAZETTE_LISTING_URL = "https://gazette.govt.nz/issues"
OFFICIAL_GAZETTE_ARCHIVE_PREFIX = "corpus-legislation-nz-gazette-official"

_ARTIFACT_TYPES = {
    "issue_listing",
    "issue_page",
    "issue_pdf",
    "notice_page",
    "notice_pdf",
    "blocked_evidence",
    "html_page",
    "index_page",
    "other",
}


def normalize_official_gazette_url(url: str) -> str:
    """Normalize Gazette URLs to a stable no-trailing-slash form."""
    parsed = urlparse(url.strip())
    path = parsed.path or ""
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


class _IssueLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attributes = {key.lower(): value for key, value in attrs if value}
        href = attributes.get("href")
        if href:
            self.hrefs.append(href)


def discover_official_gazette_issue_links(
    html: str, *, base_url: str = OFFICIAL_GAZETTE_LISTING_URL
) -> list[str]:
    """Extract stable official Gazette issue links from listing HTML."""
    parser = _IssueLinkParser()
    parser.feed(html)
    discovered: list[str] = []
    seen: set[str] = set()
    base = normalize_official_gazette_url(base_url)
    for href in parser.hrefs:
        absolute = normalize_official_gazette_url(urljoin(f"{base}/", href))
        if "gazette.govt.nz" not in urlparse(absolute).netloc:
            continue
        if not absolute.startswith(OFFICIAL_GAZETTE_LISTING_URL) and "/issues" not in absolute:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        discovered.append(absolute)
    return discovered


@dataclass(frozen=True, slots=True)
class OfficialGazetteArchiveRecord:
    """Source-specific raw archive record for official Gazette material."""

    artifact_type: str
    raw_artifact_path: str
    source_url: str
    retrieved_at: str
    content_sha256: str
    rights_note: str
    source_local_id: str
    coverage_state: str
    source_id: str = OFFICIAL_GAZETTE_SOURCE_ID
    source_name: str = OFFICIAL_GAZETTE_SOURCE_NAME
    source_tier: str = OFFICIAL_GAZETTE_SOURCE_TIER
    extraction: dict[str, Any] | None = None
    http_metadata: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


def _stable_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "artifact_type": record["artifact_type"],
        "raw_artifact_path": record["raw_artifact_path"],
        "source_url": normalize_official_gazette_url(str(record["source_url"])),
        "retrieved_at": record["retrieved_at"],
        "content_sha256": record["content_sha256"],
        "rights_note": record["rights_note"],
        "source_local_id": record["source_local_id"],
        "coverage_state": record["coverage_state"],
        "source_id": record.get("source_id", OFFICIAL_GAZETTE_SOURCE_ID),
        "source_name": record.get("source_name", OFFICIAL_GAZETTE_SOURCE_NAME),
        "source_tier": record.get("source_tier", OFFICIAL_GAZETTE_SOURCE_TIER),
        "extraction": record.get("extraction"),
        "http_metadata": record.get("http_metadata"),
        "provenance": record.get("provenance"),
        "note": record.get("note"),
    }
    return {key: value for key, value in payload.items() if value is not None}


def build_official_gazette_manifest(
    records: Iterable[Mapping[str, Any]],
    *,
    source_listing_url: str = OFFICIAL_GAZETTE_LISTING_URL,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest for official Gazette raw records."""
    normalized_records: list[dict[str, Any]] = []
    for record in records:
        required = [
            "artifact_type",
            "raw_artifact_path",
            "source_url",
            "retrieved_at",
            "content_sha256",
            "rights_note",
            "source_local_id",
            "coverage_state",
        ]
        missing = [key for key in required if key not in record or record[key] in {"", None}]
        if missing:
            raise ValueError(
                f"Official Gazette manifest record is missing required keys: {missing}"
            )
        artifact_type = str(record["artifact_type"])
        if artifact_type not in _ARTIFACT_TYPES:
            raise ValueError(f"Unsupported artifact_type: {artifact_type}")
        normalized_records.append(_stable_record_payload(record))

    normalized_records.sort(
        key=lambda item: (
            str(item["artifact_type"]),
            str(item["source_url"]),
            str(item["raw_artifact_path"]),
        )
    )
    artifact_type_counts = Counter(str(record["artifact_type"]) for record in normalized_records)
    payload = {
        "schema_version": "1.0",
        "source_id": OFFICIAL_GAZETTE_SOURCE_ID,
        "source_name": OFFICIAL_GAZETTE_SOURCE_NAME,
        "source_tier": OFFICIAL_GAZETTE_SOURCE_TIER,
        "source_listing_url": normalize_official_gazette_url(source_listing_url),
        "generated_at_utc": utc_now_iso(),
        "record_count": len(normalized_records),
        "artifact_type_counts": dict(sorted(artifact_type_counts.items())),
        "records": normalized_records,
        "coverage_warning": (
            "This is a source-specific evidence layer. It is not canonical until compared "
            "with other Gazette sources and reviewed."
        ),
    }
    content_payload = {
        "schema_version": payload["schema_version"],
        "source_id": payload["source_id"],
        "source_listing_url": payload["source_listing_url"],
        "record_count": payload["record_count"],
        "artifact_type_counts": payload["artifact_type_counts"],
        "records": payload["records"],
    }
    payload["content_sha256"] = sha256_text(
        json.dumps(content_payload, sort_keys=True, ensure_ascii=False)
    )
    manifest_payload = {k: v for k, v in payload.items() if k != "manifest_sha256"}
    payload["manifest_sha256"] = sha256_text(
        json.dumps(manifest_payload, sort_keys=True, ensure_ascii=False)
    )
    if output_path:
        write_json(output_path, payload)
    return payload


def build_official_gazette_archive(
    source_dir: Path,
    output_dir: Path,
    *,
    records_jsonl: Path,
    year: str,
    source_listing_url: str = OFFICIAL_GAZETTE_LISTING_URL,
) -> dict[str, Any]:
    """Bundle official Gazette source artifacts and write the archive manifest."""
    records = read_jsonl(records_jsonl)
    if not records:
        raise RuntimeError(f"No official Gazette records found in {records_jsonl}")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_archive(
        source_dir,
        output_dir,
        year=year,
        archive_name_prefix=OFFICIAL_GAZETTE_ARCHIVE_PREFIX,
        manifest_name_prefix=OFFICIAL_GAZETTE_ARCHIVE_PREFIX,
        tar_root_name=OFFICIAL_GAZETTE_ARCHIVE_PREFIX,
        artifact_class="official_gazette_source_archive",
        publication_target="source_evidence",
        coverage_statement=(
            "Coverage is not proven complete until reconciled against the official Gazette "
            "issue inventory and reviewed against source-specific rights boundaries."
        ),
    )
    manifest_path = output_dir / f"{OFFICIAL_GAZETTE_ARCHIVE_PREFIX}-{year}.official-manifest.json"
    manifest = build_official_gazette_manifest(
        records,
        source_listing_url=source_listing_url,
        output_path=manifest_path,
    )
    provenance_path = (
        output_dir / f"{OFFICIAL_GAZETTE_ARCHIVE_PREFIX}-{year}.official-evidence.json"
    )
    build_release_evidence(
        artifact_class="official_gazette_source_archive",
        output_path=provenance_path,
        subjects=[Path(bundle["archive_path"]), manifest_path],
        manifest=manifest,
        coverage_statement=(
            "Official Gazette source archive evidence is source-specific and must remain "
            "independent from canonical comparison outputs."
        ),
        publication_target="source_evidence",
    )
    checksums_path = output_dir / f"{OFFICIAL_GAZETTE_ARCHIVE_PREFIX}-{year}.SHA256SUMS.txt"
    lines = [
        f"{sha256_file(Path(bundle['archive_path']))}  {Path(bundle['archive_path']).name}",
        f"{sha256_file(manifest_path)}  {manifest_path.name}",
        f"{sha256_file(provenance_path)}  {provenance_path.name}",
    ]
    checksums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        **bundle,
        "manifest_path": str(manifest_path),
        "provenance_path": str(provenance_path),
        "checksums_path": str(checksums_path),
        "official_manifest_sha256": manifest["manifest_sha256"],
        "official_manifest_content_sha256": manifest["content_sha256"],
    }
