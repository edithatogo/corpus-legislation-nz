from __future__ import annotations

import html
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from typing_extensions import override

from .archive import build_archive
from .artifact_provenance import build_release_evidence
from .utils import (
    read_jsonl,
    sha256_file,
    sha256_text,
    utc_now_iso,
    write_json,
    write_jsonl,
)

HISTORICAL_GAZETTE_SOURCE_ID = "victoria_lexisnexis_gazette"
HISTORICAL_GAZETTE_SOURCE_NAME = "Victoria University / LexisNexis historical Gazette archive"
HISTORICAL_GAZETTE_SOURCE_TIER = "historical"
HISTORICAL_GAZETTE_SOURCE_INDEX_URL = (
    "https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html"
)
HISTORICAL_GAZETTE_ARCHIVE_PREFIX = "corpus-legislation-nz-gazette-victoria-lexisnexis"

_YEAR_LINK_PATTERN = re.compile(r"^(?P<year>\d{4})\.html$", re.IGNORECASE)
_ISSUE_ROW_PATTERN = re.compile(
    r"(?P<issue>\d{3})\s+(?P<label>\d{1,2}-[A-Za-z]{3})\s+p\.\s+(?P<page>\d+)"
)
_STABLE_ID_PATTERN = re.compile(r"^gazette-victoria-lexisnexis-\d{4}(-index|-\d{3})$")


def normalize_historical_gazette_url(url: str) -> str:
    """Normalize historical Gazette URLs to a stable no-trailing-slash form."""
    parsed = urlparse(url.strip())
    path = parsed.path or ""
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


class _HistoricalGazetteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.text_chunks: list[str] = []

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attributes = {key.lower(): value for key, value in attrs if value}
        href = attributes.get("href")
        if href:
            self.hrefs.append(href)

    @override
    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text_chunks.append(data)


def _strip_html_text(html_text: str) -> str:
    parser = _HistoricalGazetteParser()
    parser.feed(html_text)
    text = html.unescape(" ".join(parser.text_chunks))
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def discover_historical_gazette_year_links(
    html_text: str,
    *,
    base_url: str = HISTORICAL_GAZETTE_SOURCE_INDEX_URL,
) -> list[str]:
    """Extract stable historical Gazette year links from archive HTML."""
    parser = _HistoricalGazetteParser()
    parser.feed(html_text)
    discovered: list[str] = []
    seen: set[str] = set()
    base = normalize_historical_gazette_url(base_url)
    base_dir = base.rsplit("/", 1)[0] + "/" if "/" in base else base
    for href in parser.hrefs:
        parsed = urlparse(href)
        match = _YEAR_LINK_PATTERN.match(Path(parsed.path).name)
        if not match:
            continue
        parsed_absolute = urlparse(normalize_historical_gazette_url(urljoin(base_dir, href)))
        absolute = urlunparse(
            (
                parsed_absolute.scheme,
                parsed_absolute.netloc,
                parsed_absolute.path,
                parsed_absolute.params,
                parsed_absolute.query,
                "",
            )
        )
        if "victoria.ac.nz" not in urlparse(absolute).netloc:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        discovered.append(absolute)
    return discovered


def extract_historical_gazette_issue_rows(
    html_text: str,
    *,
    year: str,
    source_index_url: str = HISTORICAL_GAZETTE_SOURCE_INDEX_URL,
) -> list[dict[str, Any]]:
    """Extract issue/page rows from a historical Gazette year page."""
    text = _strip_html_text(html_text)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    normalized_index_url = normalize_historical_gazette_url(source_index_url)
    for match in _ISSUE_ROW_PATTERN.finditer(text):
        issue = match.group("issue")
        stable_id = f"gazette-victoria-lexisnexis-{year}-{issue}"
        if stable_id in seen:
            continue
        seen.add(stable_id)
        page_number = int(match.group("page"))
        issue_label = match.group("label")
        rows.append(
            {
                "stable_id": stable_id,
                "source_local_id": f"{year}-{issue}",
                "source_url": f"{normalized_index_url}#issue-{issue}",
                "issue_number": issue,
                "issue_label": issue_label,
                "page_start": page_number,
                "page_end": page_number,
                "row_text": match.group(0),
            }
        )
    return rows


@dataclass(frozen=True, slots=True)
class HistoricalGazetteArchiveRecord:
    """Source-specific raw archive record for historical Gazette material."""

    stable_id: str
    source_id: str
    source_name: str
    source_tier: str
    record_kind: str
    source_url: str
    retrieval_method: str
    retrieved_at: str
    content_sha256: str
    raw_artifact_path: str
    rights_note: str
    source_local_id: str
    coverage_state: str
    extraction: dict[str, Any] | None = None
    http_metadata: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


def _stable_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "stable_id": record["stable_id"],
        "source_id": record.get("source_id", HISTORICAL_GAZETTE_SOURCE_ID),
        "source_name": record.get("source_name", HISTORICAL_GAZETTE_SOURCE_NAME),
        "source_tier": record.get("source_tier", HISTORICAL_GAZETTE_SOURCE_TIER),
        "record_kind": record["record_kind"],
        "source_url": normalize_historical_gazette_url(str(record["source_url"])),
        "retrieval_method": record["retrieval_method"],
        "retrieved_at": record["retrieved_at"],
        "content_sha256": record["content_sha256"],
        "raw_artifact_path": record["raw_artifact_path"],
        "rights_note": record["rights_note"],
        "source_local_id": record["source_local_id"],
        "coverage_state": record["coverage_state"],
        "extraction": record.get("extraction"),
        "http_metadata": record.get("http_metadata"),
        "provenance": record.get("provenance"),
        "note": record.get("note"),
    }
    return {key: value for key, value in payload.items() if value is not None}


def build_historical_gazette_manifest(
    *,
    source_records: Iterable[Mapping[str, Any]],
    source_year: str,
    source_index_url: str = HISTORICAL_GAZETTE_SOURCE_INDEX_URL,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest for historical Gazette raw records."""
    normalized_records: list[dict[str, Any]] = []
    for record in source_records:
        required = [
            "stable_id",
            "record_kind",
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
                f"Historical Gazette manifest record is missing required keys: {missing}"
            )
        stable_id = str(record["stable_id"])
        if not _STABLE_ID_PATTERN.match(stable_id):
            raise ValueError(f"Unstable historical Gazette stable_id: {stable_id}")
        normalized_records.append(_stable_record_payload(record))

    normalized_records.sort(
        key=lambda item: (
            str(item["record_kind"]),
            str(item["source_url"]),
            str(item["stable_id"]),
        )
    )
    record_kind_counts = Counter(str(record["record_kind"]) for record in normalized_records)
    historical_year_counts = Counter(
        str(record.get("extraction", {}).get("historical_year"))
        for record in normalized_records
        if str(record.get("extraction", {}).get("historical_year") or "").strip()
    )
    payload = {
        "schema_version": "1.0",
        "source_id": HISTORICAL_GAZETTE_SOURCE_ID,
        "source_name": HISTORICAL_GAZETTE_SOURCE_NAME,
        "source_tier": HISTORICAL_GAZETTE_SOURCE_TIER,
        "source_year": source_year,
        "source_index_url": normalize_historical_gazette_url(source_index_url),
        "generated_at_utc": utc_now_iso(),
        "record_count": len(normalized_records),
        "record_kind_counts": dict(sorted(record_kind_counts.items())),
        "historical_year_counts": dict(sorted(historical_year_counts.items())),
        "index_page_count": record_kind_counts.get("historical_index", 0),
        "issue_row_count": record_kind_counts.get("historical_page", 0),
        "rights_warning": (
            "Historical Gazette records retain rights and access caveats on every record."
        ),
        "access_warning": (
            "Rights and access must be reviewed before any broad retrieval; this archive "
            "defaults to bounded evidence capture only."
        ),
        "coverage_warning": (
            "This is a historical source-specific evidence layer. It is not canonical and "
            "must remain separate from official, DigitalNZ, and NZLII raw archives."
        ),
        "records": normalized_records,
    }
    content_payload = {
        "schema_version": payload["schema_version"],
        "source_id": payload["source_id"],
        "source_year": payload["source_year"],
        "source_index_url": payload["source_index_url"],
        "record_count": payload["record_count"],
        "record_kind_counts": payload["record_kind_counts"],
        "historical_year_counts": payload["historical_year_counts"],
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


def build_historical_gazette_review(
    *,
    source_records: Iterable[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    source_records_path: Path,
    records_path: Path,
    raw_index_dir: Path,
    state_path: Path,
) -> dict[str, Any]:
    """Review historical Gazette evidence for rights, IDs, and provenance completeness."""
    records = list(source_records)
    missing_rights = 0
    missing_source_url = 0
    missing_hash = 0
    unstable_source_id = 0
    missing_year_page_reference = 0
    historical_only_candidates: list[str] = []

    for record in records:
        rights_note = str(record.get("rights_note") or "").strip().lower()
        if not rights_note or not any(token in rights_note for token in ("historical", "rights")):
            missing_rights += 1
        if not str(record.get("source_url") or "").strip():
            missing_source_url += 1
        if not str(record.get("content_sha256") or "").strip():
            missing_hash += 1

        stable_id = str(record.get("stable_id") or "")
        if not _STABLE_ID_PATTERN.match(stable_id):
            unstable_source_id += 1

        extraction = record.get("extraction")
        if not isinstance(extraction, dict):
            extraction = {}
        historical_year = str(extraction.get("historical_year") or "").strip()
        issue_number = str(extraction.get("issue_number") or "").strip()
        page_start = extraction.get("page_start")
        if str(record.get("record_kind")) != "historical_index" and (
            not historical_year or not (issue_number or page_start)
        ):
            missing_year_page_reference += 1

        note = str(record.get("note") or "").lower()
        if "historical-only" in note or str(record.get("record_kind")) != "historical_index":
            historical_only_candidates.append(stable_id)

    manifest_sha256 = str(manifest.get("manifest_sha256") or "").strip()
    content_sha256 = str(manifest.get("content_sha256") or "").strip()
    missing_manifest_hash = int(not manifest_sha256 or not content_sha256)
    ok = not any(
        [
            missing_rights,
            missing_source_url,
            missing_hash,
            unstable_source_id,
            missing_year_page_reference,
            missing_manifest_hash,
        ]
    )
    coverage_warning = (
        "Historical Gazette archive sample only; rights/access and comparison gates "
        "remain required before broader retrieval."
    )
    if not ok:
        coverage_warning = (
            "Historical Gazette review failed. "
            f"rights={missing_rights}, source_url={missing_source_url}, "
            f"hash={missing_hash}, unstable_ids={unstable_source_id}, "
            f"missing_year_or_page={missing_year_page_reference}, "
            f"manifest_hash_missing={missing_manifest_hash}."
        )

    return {
        "schema_version": "1.0",
        "ok": ok,
        "record_count": len(records),
        "missing_rights_count": missing_rights,
        "missing_source_url_count": missing_source_url,
        "missing_hash_count": missing_hash,
        "unstable_source_id_count": unstable_source_id,
        "missing_year_page_reference_count": missing_year_page_reference,
        "historical_only_candidate_count": len(historical_only_candidates),
        "historical_only_candidate_stable_ids": sorted(historical_only_candidates),
        "manifest_sha256": manifest_sha256,
        "content_sha256": content_sha256,
        "source_records_path": str(source_records_path),
        "records_path": str(records_path),
        "raw_index_dir": str(raw_index_dir),
        "state_path": str(state_path),
        "coverage_warning": coverage_warning,
    }


def build_historical_gazette_coverage_report(
    *,
    source_records: Iterable[Mapping[str, Any]],
    review: Mapping[str, Any],
    manifest: Mapping[str, Any],
    source_year: str,
    source_index_url: str,
) -> dict[str, Any]:
    """Summarize the historical Gazette archive coverage and review state."""
    records = list(source_records)
    coverage = {
        "schema_version": "1.0",
        "source_id": HISTORICAL_GAZETTE_SOURCE_ID,
        "source_name": HISTORICAL_GAZETTE_SOURCE_NAME,
        "source_tier": HISTORICAL_GAZETTE_SOURCE_TIER,
        "source_year": source_year,
        "source_index_url": normalize_historical_gazette_url(source_index_url),
        "record_count": len(records),
        "index_page_count": int(manifest.get("index_page_count") or 0),
        "issue_row_count": int(manifest.get("issue_row_count") or 0),
        "record_kind_counts": manifest.get("record_kind_counts") or {},
        "historical_year_counts": manifest.get("historical_year_counts") or {},
        "historical_only_candidate_count": int(review.get("historical_only_candidate_count") or 0),
        "missing_rights_count": int(review.get("missing_rights_count") or 0),
        "missing_source_url_count": int(review.get("missing_source_url_count") or 0),
        "missing_hash_count": int(review.get("missing_hash_count") or 0),
        "missing_year_page_reference_count": int(
            review.get("missing_year_page_reference_count") or 0
        ),
        "unstable_source_id_count": int(review.get("unstable_source_id_count") or 0),
        "rights_covered_count": len(records) - int(review.get("missing_rights_count") or 0),
        "coverage_warning": str(review.get("coverage_warning") or ""),
    }
    coverage["content_sha256"] = sha256_text(
        json.dumps(coverage, sort_keys=True, ensure_ascii=False)
    )
    coverage["manifest_sha256"] = sha256_text(
        json.dumps({k: v for k, v in coverage.items() if k != "manifest_sha256"}, sort_keys=True, ensure_ascii=False)
    )
    return coverage


def _historical_record(
    *,
    year: str,
    raw_artifact_path: Path,
    content_path: Path | None = None,
    source_index_url: str,
    rights_note: str,
    retrieved_at: str,
    record_kind: str,
    source_local_id: str,
    stable_id: str,
    coverage_state: str,
    extraction: dict[str, Any],
    note: str,
    source_url_suffix: str = "",
) -> HistoricalGazetteArchiveRecord:
    content_source = content_path or raw_artifact_path
    content_sha256 = sha256_file(content_source)
    return HistoricalGazetteArchiveRecord(
        stable_id=stable_id,
        source_id=HISTORICAL_GAZETTE_SOURCE_ID,
        source_name=HISTORICAL_GAZETTE_SOURCE_NAME,
        source_tier=HISTORICAL_GAZETTE_SOURCE_TIER,
        record_kind=record_kind,
        source_url=normalize_historical_gazette_url(source_index_url) + source_url_suffix,
        retrieval_method="historical_index_parse",
        retrieved_at=retrieved_at,
        content_sha256=content_sha256,
        raw_artifact_path=raw_artifact_path.as_posix(),
        rights_note=rights_note,
        source_local_id=source_local_id,
        coverage_state=coverage_state,
        extraction={"historical_year": year, **extraction},
        http_metadata={"status_code": 200, "content_type": "text/html"},
        provenance={
            "pipeline_name": "historical-gazette",
            "pipeline_version": "1.0.0",
            "source_name": HISTORICAL_GAZETTE_SOURCE_NAME,
            "source_record_id": source_local_id,
            "source_retrieved_at": retrieved_at,
            "release_version": "1.0.0",
            "release_commit": "local-dev",
            "license_note": rights_note,
        },
        note=note,
    )


def export_historical_gazette_source(
    *,
    output_dir: Path,
    source_year: str = "2008",
    source_index_url: str = HISTORICAL_GAZETTE_SOURCE_INDEX_URL,
    index_html_path: Path | None = None,
    max_issue_rows: int | None = None,
    rights_note: str = (
        "Historical Victoria/LexisNexis archive capture. Rights and access caveats "
        "remain attached to every record."
    ),
    access_note: str = (
        "Historical archive access is bounded, identifiable, and fail-closed when "
        "the archive surface is unavailable or unclear."
    ),
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Run a bounded historical Gazette export and write raw and normalized artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_index_dir = output_dir / "raw" / "index"
    manifests_dir = output_dir / "manifests"
    state_dir = output_dir / "_state"
    raw_index_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    if index_html_path is not None:
        raw_bytes = index_html_path.read_bytes()
        retrieval_method = "local-file"
    else:
        headers = {"User-Agent": "nzlc-historical-gazette-archive/1.0"}
        client = session or requests.Session()
        try:
            response = client.get(
                normalize_historical_gazette_url(source_index_url), headers=headers
            )
            response.raise_for_status()
            raw_bytes = response.content
        finally:
            if session is None:
                client.close()
        retrieval_method = "http-get"

    retrieved_at = utc_now_iso()
    raw_index_path = raw_index_dir / f"{source_year}.html"
    raw_index_path.write_bytes(raw_bytes)
    html_text = raw_bytes.decode("utf-8", errors="replace")
    year_links = discover_historical_gazette_year_links(html_text, base_url=source_index_url)
    issue_rows = extract_historical_gazette_issue_rows(
        html_text,
        year=source_year,
        source_index_url=source_index_url,
    )
    if max_issue_rows is not None:
        issue_rows = issue_rows[:max_issue_rows]

    source_records: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    index_record = _historical_record(
        year=source_year,
        raw_artifact_path=raw_index_path.relative_to(output_dir),
        content_path=raw_index_path,
        source_index_url=source_index_url,
        rights_note=rights_note,
        retrieved_at=retrieved_at,
        record_kind="historical_index",
        source_local_id=f"{source_year}-index",
        stable_id=f"gazette-victoria-lexisnexis-{source_year}-index",
        coverage_state="partial",
        extraction={
            "year_links": year_links,
            "year_link_count": len(year_links),
            "issue_row_count": len(issue_rows),
            "retrieval_method": retrieval_method,
            "access_note": access_note,
            "source_index_url": normalize_historical_gazette_url(source_index_url),
        },
        note="Historical archive index capture.",
    )
    source_records.append(index_record.to_dict())
    records.append(index_record.to_dict())

    for row in issue_rows:
        issue_number = str(row["issue_number"])
        source_local_id = str(row["source_local_id"])
        record = _historical_record(
            year=source_year,
            raw_artifact_path=raw_index_path.relative_to(output_dir),
            content_path=raw_index_path,
            source_index_url=source_index_url,
            rights_note=rights_note,
            retrieved_at=retrieved_at,
            record_kind="historical_page",
            source_local_id=source_local_id,
        stable_id=str(row["stable_id"]),
        coverage_state="partial",
        extraction={
                "issue_number": issue_number,
                "issue_label": row["issue_label"],
                "page_start": row["page_start"],
                "page_end": row["page_end"],
                "row_text": row["row_text"],
                "source_index_url": normalize_historical_gazette_url(source_index_url),
                "year_links": year_links,
            },
            note="Historical-only candidate extracted from the archive table of contents.",
            source_url_suffix=f"#issue-{issue_number}",
        )
        source_records.append(record.to_dict())
        records.append(record.to_dict())

    source_records_path = output_dir / "source_records.jsonl"
    records_path = output_dir / "records.jsonl"
    state_path = state_dir / "export_state.json"
    validation_path = manifests_dir / "validation_report.json"
    coverage_path = manifests_dir / "coverage_report.json"
    manifest_path = manifests_dir / "latest_manifest.json"

    source_records_sorted = sorted(source_records, key=lambda row: str(row["stable_id"]))
    records_sorted = sorted(records, key=lambda row: str(row["stable_id"]))
    write_jsonl(source_records_path, source_records_sorted)
    write_jsonl(records_path, records_sorted)

    manifest = build_historical_gazette_manifest(
        source_records=source_records_sorted,
        source_year=source_year,
        source_index_url=source_index_url,
        output_path=manifest_path,
    )
    review = build_historical_gazette_review(
        source_records=source_records_sorted,
        manifest=manifest,
        source_records_path=source_records_path,
        records_path=records_path,
        raw_index_dir=raw_index_dir,
        state_path=state_path,
    )
    coverage = build_historical_gazette_coverage_report(
        source_records=source_records_sorted,
        review=review,
        manifest=manifest,
        source_year=source_year,
        source_index_url=source_index_url,
    )
    write_json(validation_path, review)
    write_json(coverage_path, coverage)
    write_json(
        state_path,
        {
            "source_index_url": normalize_historical_gazette_url(source_index_url),
            "source_year": source_year,
            "retrieved_at_utc": retrieved_at,
            "raw_record_count": len(source_records_sorted),
            "record_count": len(records_sorted),
            "index_page_count": 1,
            "issue_row_count": len(issue_rows),
            "year_link_count": len(year_links),
            "rights_caveat_count": len(source_records_sorted),
            "historical_only_candidate_count": review["historical_only_candidate_count"],
            "validation_ok": review["ok"],
            "retrieval_method": retrieval_method,
            "access_note": access_note,
        },
    )
    return {
        "ok": review["ok"],
        "source_year": source_year,
        "source_index_url": normalize_historical_gazette_url(source_index_url),
        "source_records_path": str(source_records_path),
        "records_path": str(records_path),
        "raw_index_dir": str(raw_index_dir),
        "state_path": str(state_path),
        "manifest_path": str(manifest_path),
        "validation_path": str(validation_path),
        "coverage_path": str(coverage_path),
        "archive_index_path": str(raw_index_path),
        "raw_record_count": len(source_records_sorted),
        "record_count": len(records_sorted),
        "index_page_count": 1,
        "issue_row_count": len(issue_rows),
        "year_link_count": len(year_links),
        "review": review,
        "manifest": manifest,
        "coverage": coverage,
    }


def build_historical_gazette_archive(
    source_dir: Path,
    output_dir: Path,
    *,
    records_jsonl: Path,
    year: str,
    source_index_url: str = HISTORICAL_GAZETTE_SOURCE_INDEX_URL,
) -> dict[str, Any]:
    """Bundle historical Gazette source artifacts and write the archive manifest."""
    records = read_jsonl(records_jsonl)
    if not records:
        raise RuntimeError(f"No historical Gazette records found in {records_jsonl}")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_archive(
        source_dir,
        output_dir,
        year=year,
        archive_name_prefix=HISTORICAL_GAZETTE_ARCHIVE_PREFIX,
        manifest_name_prefix=HISTORICAL_GAZETTE_ARCHIVE_PREFIX,
        tar_root_name=HISTORICAL_GAZETTE_ARCHIVE_PREFIX,
        artifact_class="historical_gazette_source_archive",
        publication_target="source_evidence",
        coverage_statement=(
            "Historical Gazette source archive evidence is rights-caveated and "
            "must remain independent from canonical comparison outputs."
        ),
    )
    manifest_path = (
        output_dir / f"{HISTORICAL_GAZETTE_ARCHIVE_PREFIX}-{year}.historical-manifest.json"
    )
    manifest = build_historical_gazette_manifest(
        source_records=records,
        source_year=year,
        source_index_url=source_index_url,
        output_path=manifest_path,
    )
    provenance_path = (
        output_dir / f"{HISTORICAL_GAZETTE_ARCHIVE_PREFIX}-{year}.historical-evidence.json"
    )
    build_release_evidence(
        artifact_class="historical_gazette_source_archive",
        output_path=provenance_path,
        subjects=[Path(bundle["archive_path"]), manifest_path],
        manifest=manifest,
        coverage_statement=(
            "Historical Gazette source archive evidence is historical and rights-caveated; "
            "it must remain independent from canonical comparison outputs."
        ),
        publication_target="source_evidence",
    )
    checksums_path = (
        output_dir / f"{HISTORICAL_GAZETTE_ARCHIVE_PREFIX}-{year}.SHA256SUMS.txt"
    )
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
        "historical_manifest_sha256": manifest["manifest_sha256"],
        "historical_manifest_content_sha256": manifest["content_sha256"],
    }
