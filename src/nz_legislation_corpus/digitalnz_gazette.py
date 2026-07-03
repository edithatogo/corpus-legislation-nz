"""DigitalNZ New Zealand Gazette archive helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

from .archive import build_archive
from .artifact_provenance import build_release_evidence
from .utils import (
    read_json,
    read_jsonl,
    sha256_file,
    sha256_text,
    slug_for_path,
    utc_now_iso,
    write_json,
    write_jsonl,
)

DIGITALNZ_GAZETTE_SOURCE_ID = "digitalnz_gazette"
DIGITALNZ_GAZETTE_SOURCE_NAME = "DigitalNZ Gazette discovery/export"
DIGITALNZ_GAZETTE_SOURCE_TIER = "discovery"
DIGITALNZ_GAZETTE_SOURCE_LISTING_URL = "https://digitalnz.org/"
DIGITALNZ_GAZETTE_API_URL = "https://api.digitalnz.org/v3/records.json"
DIGITALNZ_GAZETTE_ARCHIVE_PREFIX = "corpus-legislation-nz-gazette-digitalnz"
DIGITALNZ_GAZETTE_DNZ_ISSUE_URL = "https://github.com/edithatogo/dnz/issues/1"
DEFAULT_GAZETTE_QUERY_TEXT = "Gazette"
DEFAULT_GAZETTE_COLLECTION = "New Zealand Gazette"
DEFAULT_GAZETTE_SORT_FIELD = "date"
DEFAULT_GAZETTE_SORT_DIRECTION = "asc"

_REQUIRED_RIGHTS_HINTS = ("rights", "license", "licence", "rights_url", "rights_statement")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _first_text(value: Any) -> str:
    values = _as_list(value)
    return values[0] if values else ""


def _landing_url_for_record(record: dict[str, Any]) -> str:
    landing = (
        str(record.get("display_url") or "")
        or str(record.get("url") or "")
        or str(record.get("source_url") or "")
    )
    if landing.strip():
        return landing.strip()
    record_id = str(record.get("id") or "").strip()
    if record_id:
        return urljoin(DIGITALNZ_GAZETTE_SOURCE_LISTING_URL, f"records/{record_id}")
    return DIGITALNZ_GAZETTE_SOURCE_LISTING_URL


def _original_source_url_for_record(record: dict[str, Any]) -> str | None:
    source_url = str(record.get("source_url") or "").strip()
    return source_url or None


def _rights_metadata(record: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key in _REQUIRED_RIGHTS_HINTS:
        value = record.get(key)
        if value not in {None, ""}:
            metadata[key] = value
    return metadata


def _rights_note_for_record(record: dict[str, Any]) -> str:
    metadata = _rights_metadata(record)
    if metadata:
        return _first_text(
            metadata.get("rights_statement")
            or metadata.get("rights")
            or metadata.get("licence")
            or metadata.get("license")
            or metadata.get("rights_url")
        )
    return (
        "DigitalNZ Gazette discovery metadata is source evidence only; "
        "rights/licence details must be preserved or triaged separately."
    )


def _record_kind_for_record() -> str:
    return "digitalnz_item"


@dataclass(frozen=True, slots=True)
class DigitalNZGazetteQueryPlan:
    """Deterministic DigitalNZ Gazette paging plan."""

    query_text: str
    collection_filter: str
    page_size: int
    start_page: int
    max_pages: int | None
    sort_field: str
    sort_direction: str
    api_access_mode: str
    api_url: str
    dnz_issue_url: str
    dnz_repo_root: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["query_sha256"] = sha256_text(
            _stable_json(
                {
                    "query_text": self.query_text,
                    "collection_filter": self.collection_filter,
                    "page_size": self.page_size,
                    "start_page": self.start_page,
                    "max_pages": self.max_pages,
                    "sort_field": self.sort_field,
                    "sort_direction": self.sort_direction,
                    "api_access_mode": self.api_access_mode,
                    "api_url": self.api_url,
                    "dnz_issue_url": self.dnz_issue_url,
                    "dnz_repo_root": self.dnz_repo_root,
                }
            )
        )
        return payload


def build_digitalnz_gazette_query_plan(
    *,
    query_text: str = DEFAULT_GAZETTE_QUERY_TEXT,
    collection_filter: str = DEFAULT_GAZETTE_COLLECTION,
    page_size: int = 100,
    start_page: int = 1,
    max_pages: int | None = None,
    sort_field: str = DEFAULT_GAZETTE_SORT_FIELD,
    sort_direction: str = DEFAULT_GAZETTE_SORT_DIRECTION,
    api_access_mode: str = "key_required",
    api_url: str = DIGITALNZ_GAZETTE_API_URL,
    dnz_issue_url: str = DIGITALNZ_GAZETTE_DNZ_ISSUE_URL,
    dnz_repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic paging plan for the Gazette DigitalNZ export."""
    plan = DigitalNZGazetteQueryPlan(
        query_text=query_text.strip(),
        collection_filter=collection_filter.strip(),
        page_size=max(1, int(page_size)),
        start_page=max(1, int(start_page)),
        max_pages=max_pages if max_pages is None else max(1, int(max_pages)),
        sort_field=sort_field.strip(),
        sort_direction=sort_direction.strip().lower() or DEFAULT_GAZETTE_SORT_DIRECTION,
        api_access_mode=api_access_mode.strip() or "key_required",
        api_url=api_url.strip(),
        dnz_issue_url=dnz_issue_url.strip(),
        dnz_repo_root=str(dnz_repo_root) if dnz_repo_root else None,
    )
    return plan.to_dict()


def _query_params_for_plan(plan: dict[str, Any], page: int, api_key: str) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = [
        ("api_key", api_key),
        ("text", str(plan["query_text"])),
        ("page", str(page)),
        ("per_page", str(plan["page_size"])),
        ("sort", str(plan["sort_field"])),
        ("direction", str(plan["sort_direction"])),
        ("and[primary_collection][]", str(plan["collection_filter"])),
    ]
    return params


def _fetch_digitalnz_page(
    *,
    plan: dict[str, Any],
    page: int,
    api_key: str,
    session: requests.Session | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    client = session or requests.Session()
    params = _query_params_for_plan(plan, page, api_key)
    response = client.get(
        plan["api_url"],
        params=params,
        timeout=30,
        headers={
            "Accept": "application/json",
            "User-Agent": "corpus-legislation-nz-digitalnz-gazette-export/1.0",
        },
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("DigitalNZ response was not a JSON object")
    search_block = payload.get("search") if isinstance(payload.get("search"), dict) else payload
    result_count = int(search_block.get("result_count") or 0)
    results = search_block.get("results") or []
    if not isinstance(results, list):
        raise RuntimeError("DigitalNZ response did not contain a results array")
    meta = {
        "requested_page": page,
        "api_url": plan["api_url"],
        "query_sha256": plan["query_sha256"],
        "result_count": result_count,
        "returned_count": len(results),
        "retrieved_at_utc": utc_now_iso(),
        "request_sha256": sha256_text(_stable_json({"api_url": plan["api_url"], "params": params})),
        "response_sha256": sha256_text(_stable_json(payload)),
    }
    return payload, meta


def _normalized_record(
    *,
    item: dict[str, Any],
    plan: dict[str, Any],
    page_meta: dict[str, Any],
    page_number: int,
    page_position: int,
    raw_page_path: Path,
    raw_item_path: Path,
    source_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    item_id = str(item.get("id") or "").strip()
    title = str(item.get("title") or "").strip()
    description = item.get("description")
    landing_url = _landing_url_for_record(item)
    original_source_url = _original_source_url_for_record(item)
    record_sha256 = sha256_text(_stable_json(item))
    rights_metadata = _rights_metadata(item)
    rights_note = _rights_note_for_record(item)
    source_local_id = item_id or slug_for_path(landing_url)
    stable_id = f"digitalnz-gazette-{slug_for_path(source_local_id)}"
    date_values = _as_list(item.get("date"))
    collection_values = _as_list(item.get("collection"))
    content_partner_values = _as_list(item.get("content_partner"))
    creator_values = _as_list(item.get("creator"))
    category_values = _as_list(item.get("category"))
    text_bearing = bool(str(description or "").strip())
    normalized = {
        "stable_id": stable_id,
        "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
        "source_name": DIGITALNZ_GAZETTE_SOURCE_NAME,
        "source_tier": DIGITALNZ_GAZETTE_SOURCE_TIER,
        "record_kind": _record_kind_for_record(),
        "source_local_id": source_local_id,
        "title": title,
        "description": description or "",
        "date": date_values,
        "collection": collection_values,
        "content_partner": content_partner_values,
        "creator": creator_values,
        "category": category_values,
        "landing_url": landing_url,
        "original_source_url": original_source_url,
        "source_url": original_source_url or landing_url,
        "rights_note": rights_note,
        "coverage_state": "complete" if text_bearing else "partial",
        "page_number": page_number,
        "page_position": page_position,
        "query_sha256": plan["query_sha256"],
        "query_text": plan["query_text"],
        "collection_filter": plan["collection_filter"],
        "page_size": plan["page_size"],
        "sort_field": plan["sort_field"],
        "sort_direction": plan["sort_direction"],
        "api_access_mode": plan["api_access_mode"],
        "page_request_sha256": page_meta["request_sha256"],
        "page_response_sha256": page_meta["response_sha256"],
        "content_sha256": record_sha256,
        "raw_artifact_path": raw_item_path.as_posix(),
        "raw_page_path": raw_page_path.as_posix(),
        "retrieved_at": page_meta["retrieved_at_utc"],
        "source_manifest_sha256": source_manifest_sha256,
        "extraction": {
            "landing_url": landing_url,
            "original_source_url": original_source_url,
            "text_bearing": text_bearing,
            "rights_metadata": rights_metadata,
            "query_sha256": plan["query_sha256"],
            "query_text": plan["query_text"],
            "collection_filter": plan["collection_filter"],
            "page_number": page_number,
            "page_position": page_position,
            "page_request_sha256": page_meta["request_sha256"],
            "page_response_sha256": page_meta["response_sha256"],
            "api_url": page_meta["api_url"],
            "source_manifest_sha256": source_manifest_sha256,
        },
    }
    return {
        key: value
        for key, value in normalized.items()
        if (value is not None and value != "")
        or key in {"description", "source_manifest_sha256"}
    }


def normalize_digitalnz_gazette_item(
    *,
    item: dict[str, Any],
    plan: dict[str, Any],
    page_meta: dict[str, Any],
    page_number: int,
    page_position: int,
    raw_page_path: Path,
    raw_item_path: Path,
    source_manifest_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the raw and normalized records for a single DigitalNZ result item."""
    normalized = _normalized_record(
        item=item,
        plan=plan,
        page_meta=page_meta,
        page_number=page_number,
        page_position=page_position,
        raw_page_path=raw_page_path,
        raw_item_path=raw_item_path,
        source_manifest_sha256=source_manifest_sha256,
    )
    return (
        _raw_source_record(
            item=item,
            normalized_record=normalized,
            plan=plan,
            page_meta=page_meta,
            raw_item_path=raw_item_path,
            raw_page_path=raw_page_path,
            source_manifest_sha256=source_manifest_sha256,
        ),
        normalized,
    )


def _raw_source_record(
    *,
    item: dict[str, Any],
    normalized_record: dict[str, Any],
    plan: dict[str, Any],
    page_meta: dict[str, Any],
    raw_item_path: Path,
    raw_page_path: Path,
    source_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    rights_metadata = normalized_record.get("extraction", {}).get("rights_metadata", {})
    source_url = normalized_record.get("source_url") or normalized_record.get("landing_url")
    provenance = {
        "pipeline_name": "digitalnz-gazette-export",
        "pipeline_version": "1.0",
        "source_name": DIGITALNZ_GAZETTE_SOURCE_NAME,
        "source_record_id": normalized_record["stable_id"],
        "source_retrieved_at": page_meta["retrieved_at_utc"],
        "release_version": "1.0",
        "release_commit": "0000000",
        "license_note": normalized_record["rights_note"],
        "query_sha256": plan["query_sha256"],
        "api_access_mode": plan["api_access_mode"],
        "page_number": page_meta["requested_page"],
        "page_request_sha256": page_meta["request_sha256"],
        "page_response_sha256": page_meta["response_sha256"],
        "source_manifest_sha256": source_manifest_sha256,
    }
    return {
        "stable_id": normalized_record["stable_id"],
        "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
        "source_name": DIGITALNZ_GAZETTE_SOURCE_NAME,
        "source_tier": DIGITALNZ_GAZETTE_SOURCE_TIER,
        "record_kind": _record_kind_for_record(),
        "source_url": source_url,
        "retrieval_method": "digitalnz_api_v3_search",
        "retrieved_at": page_meta["retrieved_at_utc"],
        "content_sha256": normalized_record["content_sha256"],
        "raw_artifact_path": raw_item_path.as_posix(),
        "rights_note": normalized_record["rights_note"],
        "source_local_id": normalized_record["source_local_id"],
        "coverage_state": normalized_record["coverage_state"],
        "http_metadata": {
            "api_url": page_meta["api_url"],
            "page_number": page_meta["requested_page"],
            "page_position": normalized_record["page_position"],
            "request_sha256": page_meta["request_sha256"],
            "response_sha256": page_meta["response_sha256"],
            "landing_url": normalized_record.get("landing_url"),
            "original_source_url": normalized_record.get("source_url"),
            "content_type": "application/json",
        },
        "extraction": {
            "query_sha256": plan["query_sha256"],
            "query_text": plan["query_text"],
            "collection_filter": plan["collection_filter"],
            "page_number": page_meta["requested_page"],
            "page_position": normalized_record["page_position"],
            "landing_url": normalized_record.get("landing_url"),
            "original_source_url": normalized_record.get("source_url"),
            "title": normalized_record.get("title"),
            "description": normalized_record.get("description"),
            "date": normalized_record.get("date"),
            "collection": normalized_record.get("collection"),
            "content_partner": normalized_record.get("content_partner"),
            "creator": normalized_record.get("creator"),
            "category": normalized_record.get("category"),
            "rights_metadata": rights_metadata,
            "page_request_sha256": page_meta["request_sha256"],
            "page_response_sha256": page_meta["response_sha256"],
            "api_url": page_meta["api_url"],
            "raw_page_path": raw_page_path.as_posix(),
            "source_manifest_sha256": source_manifest_sha256,
            "raw_item_payload_sha256": sha256_text(_stable_json(item)),
        },
        "provenance": provenance,
    }


def _page_summary(
    page_number: int, raw_page_path: Path, page_meta: dict[str, Any], result_count: int
) -> dict[str, Any]:
    return {
        "page_number": page_number,
        "raw_page_path": raw_page_path.as_posix(),
        "raw_page_sha256": sha256_file(raw_page_path),
        "page_request_sha256": page_meta["request_sha256"],
        "page_response_sha256": page_meta["response_sha256"],
        "result_count": result_count,
        "retrieved_at_utc": page_meta["retrieved_at_utc"],
        "api_url": page_meta["api_url"],
    }


def build_digitalnz_gazette_manifest(
    *,
    source_records: list[dict[str, Any]],
    normalized_records: list[dict[str, Any]],
    plan: dict[str, Any],
    page_summaries: list[dict[str, Any]],
    source_records_path: Path,
    records_path: Path,
    raw_pages_dir: Path,
    state_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest for the DigitalNZ Gazette source archive."""
    source_record_summaries = [
        {
            "stable_id": row["stable_id"],
            "source_id": row["source_id"],
            "source_name": row["source_name"],
            "source_tier": row["source_tier"],
            "record_kind": row["record_kind"],
            "title": row["title"],
            "source_url": row["source_url"],
            "landing_url": row["landing_url"],
            "original_source_url": row.get("original_source_url"),
            "rights_note": row["rights_note"],
            "source_local_id": row["source_local_id"],
            "coverage_state": row["coverage_state"],
            "content_sha256": row["content_sha256"],
            "raw_artifact_path": row["raw_artifact_path"],
            "page_number": row["extraction"]["page_number"],
            "page_position": row["extraction"]["page_position"],
        }
        for row in normalized_records
    ]
    manifest_content = {
        "schema_version": "1.0",
        "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
        "source_name": DIGITALNZ_GAZETTE_SOURCE_NAME,
        "source_tier": DIGITALNZ_GAZETTE_SOURCE_TIER,
        "source_listing_url": DIGITALNZ_GAZETTE_SOURCE_LISTING_URL,
        "generated_at_utc": utc_now_iso(),
        "api_access_mode": plan["api_access_mode"],
        "dnz_dependency_issue_url": plan["dnz_issue_url"],
        "dnz_repo_root": plan.get("dnz_repo_root"),
        "query": {
            "query_text": plan["query_text"],
            "collection_filter": plan["collection_filter"],
            "page_size": plan["page_size"],
            "start_page": plan["start_page"],
            "max_pages": plan["max_pages"],
            "sort_field": plan["sort_field"],
            "sort_direction": plan["sort_direction"],
            "query_sha256": plan["query_sha256"],
            "api_url": plan["api_url"],
        },
        "page_count": len(page_summaries),
        "raw_record_count": len(source_records),
        "normalized_record_count": len(normalized_records),
        "record_count": len(normalized_records),
        "source_records_path": source_records_path.as_posix(),
        "records_path": records_path.as_posix(),
        "raw_pages_path": raw_pages_dir.as_posix(),
        "state_path": state_path.as_posix(),
        "pages": page_summaries,
        "records": source_record_summaries,
        "coverage_warning": (
            "DigitalNZ Gazette exports are corroborative source evidence. "
            "They remain distinct from official Gazette and canonical comparison layers."
        ),
    }
    manifest_content["content_sha256"] = sha256_text(
        _stable_json(
            {
                "schema_version": manifest_content["schema_version"],
                "source_id": manifest_content["source_id"],
                "query": manifest_content["query"],
                "page_count": manifest_content["page_count"],
                "raw_record_count": manifest_content["raw_record_count"],
                "normalized_record_count": manifest_content["normalized_record_count"],
                "source_records_path": manifest_content["source_records_path"],
                "records_path": manifest_content["records_path"],
                "raw_pages_path": manifest_content["raw_pages_path"],
                "state_path": manifest_content["state_path"],
                "pages": manifest_content["pages"],
                "records": manifest_content["records"],
            }
        )
    )
    manifest_content["manifest_sha256"] = sha256_text(
        _stable_json({k: v for k, v in manifest_content.items() if k != "manifest_sha256"})
    )
    if output_path:
        write_json(output_path, manifest_content)
    return manifest_content


def build_digitalnz_gazette_review(
    *,
    source_records: list[dict[str, Any]],
    normalized_records: list[dict[str, Any]],
    manifest: dict[str, Any],
    page_summaries: list[dict[str, Any]],
    source_records_path: Path,
    records_path: Path,
    raw_pages_dir: Path,
    state_path: Path,
) -> dict[str, Any]:
    """Produce a deterministic review report for the DigitalNZ Gazette export."""
    missing_rights = [
        row["stable_id"]
        for row in source_records
        if not row.get("rights_note") or not row.get("extraction", {}).get("rights_metadata")
    ]
    missing_source_url = [row["stable_id"] for row in source_records if not row.get("source_url")]
    missing_original_source_url = [
        row["stable_id"]
        for row in normalized_records
        if not row.get("original_source_url")
        and not row.get("extraction", {}).get("original_source_url")
    ]
    missing_landing_url = [
        row["stable_id"] for row in source_records if not row.get("extraction", {}).get("landing_url")
    ]
    missing_ids = [row["stable_id"] for row in source_records if not row.get("source_local_id")]
    metadata_only = [row["stable_id"] for row in normalized_records if not row.get("description")]
    text_bearing = [row["stable_id"] for row in normalized_records if row.get("description")]
    missing_manifest_hash = not manifest.get("manifest_sha256") or not manifest.get("content_sha256")
    page_mismatch = len(page_summaries) != int(manifest.get("page_count") or 0)
    count_mismatch = (
        len(source_records) != int(manifest.get("raw_record_count") or 0)
        or len(normalized_records) != int(manifest.get("normalized_record_count") or 0)
        or len(normalized_records) != int(manifest.get("record_count") or 0)
    )
    missing_artifacts = [
        path.as_posix()
        for path in [source_records_path, records_path, raw_pages_dir, state_path]
        if not path.exists()
    ]
    ok = not (
        missing_rights
        or missing_source_url
        or missing_original_source_url
        or missing_landing_url
        or missing_ids
        or missing_manifest_hash
        or page_mismatch
        or count_mismatch
        or missing_artifacts
    )
    return {
        "schema_version": "1.0",
        "ok": ok,
        "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
        "source_name": DIGITALNZ_GAZETTE_SOURCE_NAME,
        "source_tier": DIGITALNZ_GAZETTE_SOURCE_TIER,
        "manifest_sha256": manifest.get("manifest_sha256"),
        "content_sha256": manifest.get("content_sha256"),
        "page_count": len(page_summaries),
        "raw_record_count": len(source_records),
        "normalized_record_count": len(normalized_records),
        "metadata_only_count": len(metadata_only),
        "text_bearing_count": len(text_bearing),
        "missing_rights_count": len(missing_rights),
        "missing_rights_ids": missing_rights,
        "missing_source_url_count": len(missing_source_url),
        "missing_source_url_ids": missing_source_url,
        "missing_original_source_url_count": len(missing_original_source_url),
        "missing_original_source_url_ids": missing_original_source_url,
        "missing_landing_url_count": len(missing_landing_url),
        "missing_landing_url_ids": missing_landing_url,
        "missing_id_count": len(missing_ids),
        "missing_id_ids": missing_ids,
        "missing_manifest_hash": missing_manifest_hash,
        "count_mismatch": count_mismatch,
        "page_mismatch": page_mismatch,
        "missing_artifacts": missing_artifacts,
        "coverage_warning": (
            "Metadata-only DigitalNZ records are preserved as corroborative evidence; "
            "they remain distinct from fully text-bearing notices."
        ),
    }


def export_digitalnz_gazette_source(
    *,
    output_dir: Path,
    api_key: str,
    query_text: str = DEFAULT_GAZETTE_QUERY_TEXT,
    collection_filter: str = DEFAULT_GAZETTE_COLLECTION,
    page_size: int = 100,
    start_page: int = 1,
    max_pages: int | None = None,
    sort_field: str = DEFAULT_GAZETTE_SORT_FIELD,
    sort_direction: str = DEFAULT_GAZETTE_SORT_DIRECTION,
    api_access_mode: str = "key_required",
    api_url: str = DIGITALNZ_GAZETTE_API_URL,
    dnz_issue_url: str = DIGITALNZ_GAZETTE_DNZ_ISSUE_URL,
    dnz_repo_root: Path | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Run a bounded DigitalNZ Gazette export and write raw and normalized artifacts."""
    plan = build_digitalnz_gazette_query_plan(
        query_text=query_text,
        collection_filter=collection_filter,
        page_size=page_size,
        start_page=start_page,
        max_pages=max_pages,
        sort_field=sort_field,
        sort_direction=sort_direction,
        api_access_mode=api_access_mode,
        api_url=api_url,
        dnz_issue_url=dnz_issue_url,
        dnz_repo_root=dnz_repo_root,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_pages_dir = output_dir / "raw" / "pages"
    raw_items_dir = output_dir / "raw" / "items"
    manifests_dir = output_dir / "manifests"
    state_dir = output_dir / "_state"
    raw_pages_dir.mkdir(parents=True, exist_ok=True)
    raw_items_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    existing_source_records = read_jsonl(output_dir / "source_records.jsonl")
    existing_records = read_jsonl(output_dir / "records.jsonl")
    existing_page_summaries = read_jsonl(state_dir / "page_index.jsonl")
    state = read_json(state_dir / "export_state.json", default={}) or {}
    if state.get("query_sha256") and state.get("query_sha256") != plan["query_sha256"]:
        raise RuntimeError(
            "Existing export state belongs to a different DigitalNZ Gazette query. "
            "Use a fresh output directory or remove the prior state."
        )

    next_page = int(state.get("next_page") or plan["start_page"])
    completed_pages = {int(page["page_number"]) for page in existing_page_summaries}
    raw_source_records = list(existing_source_records)
    normalized_records = list(existing_records)
    page_summaries = list(existing_page_summaries)
    total_result_count = 0

    while True:
        payload, page_meta = _fetch_digitalnz_page(
            plan=plan,
            page=next_page,
            api_key=api_key,
            session=session,
        )
        search_block = payload.get("search") if isinstance(payload.get("search"), dict) else payload
        raw_results = search_block.get("results") or []
        total_result_count = int(search_block.get("result_count") or total_result_count or 0)
        raw_page_path = raw_pages_dir / f"page-{next_page:04d}.json"
        write_json(raw_page_path, payload)
        for index, item in enumerate(raw_results, start=1):
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or "").strip() or slug_for_path(
                str(item.get("title") or f"page-{next_page:04d}-{index}")
            )
            raw_item_path = raw_items_dir / f"{slug_for_path(item_id)}.json"
            write_json(raw_item_path, item)
            raw_record, normalized = normalize_digitalnz_gazette_item(
                item=item,
                plan=plan,
                page_meta=page_meta,
                page_number=next_page,
                page_position=index,
                raw_page_path=raw_page_path.relative_to(output_dir),
                raw_item_path=raw_item_path.relative_to(output_dir),
            )
            raw_source_records.append(raw_record)
            normalized_records.append(normalized)

        page_summary = _page_summary(
            next_page, raw_page_path, page_meta, len(raw_results)
        )
        page_summaries.append(page_summary)

        next_page += 1
        completed_pages.add(page_summary["page_number"])
        reached_limit = plan["max_pages"] is not None and len(page_summaries) >= int(plan["max_pages"])
        exhausted = len(raw_results) == 0
        if total_result_count and len(normalized_records) >= total_result_count:
            exhausted = True
        if reached_limit or exhausted:
            break

    source_records_path = output_dir / "source_records.jsonl"
    records_path = output_dir / "records.jsonl"
    page_index_path = state_dir / "page_index.jsonl"
    state_path = state_dir / "export_state.json"
    manifest_path = manifests_dir / "latest_manifest.json"
    validation_path = manifests_dir / "validation_report.json"
    coverage_path = manifests_dir / "coverage_report.json"

    source_records_sorted = sorted(raw_source_records, key=lambda row: str(row["stable_id"]))
    normalized_records_sorted = sorted(normalized_records, key=lambda row: str(row["stable_id"]))
    page_summaries_sorted = sorted(page_summaries, key=lambda row: int(row["page_number"]))

    write_jsonl(source_records_path, source_records_sorted)
    write_jsonl(records_path, normalized_records_sorted)
    write_jsonl(page_index_path, page_summaries_sorted)

    manifest = build_digitalnz_gazette_manifest(
        source_records=source_records_sorted,
        normalized_records=normalized_records_sorted,
        plan=plan,
        page_summaries=page_summaries_sorted,
        source_records_path=source_records_path.relative_to(output_dir),
        records_path=records_path.relative_to(output_dir),
        raw_pages_dir=raw_pages_dir.relative_to(output_dir),
        state_path=state_path.relative_to(output_dir),
        output_path=manifest_path,
    )
    write_json(
        state_path,
        {
            "query_sha256": plan["query_sha256"],
            "next_page": next_page,
            "completed_pages": sorted(completed_pages),
            "last_page": page_summaries_sorted[-1]["page_number"] if page_summaries_sorted else None,
            "last_page_retrieved_at_utc": page_summaries_sorted[-1]["retrieved_at_utc"]
            if page_summaries_sorted
            else None,
            "raw_record_count": len(source_records_sorted),
            "normalized_record_count": len(normalized_records_sorted),
            "raw_page_count": len(page_summaries_sorted),
            "result_count": total_result_count,
            "api_access_mode": plan["api_access_mode"],
            "dnz_dependency_issue_url": plan["dnz_issue_url"],
            "dnz_repo_root": plan.get("dnz_repo_root"),
        },
    )
    review = build_digitalnz_gazette_review(
        source_records=source_records_sorted,
        normalized_records=normalized_records_sorted,
        manifest=manifest,
        page_summaries=page_summaries_sorted,
        source_records_path=source_records_path,
        records_path=records_path,
        raw_pages_dir=raw_pages_dir,
        state_path=state_path,
    )
    coverage = {
        "schema_version": "1.0",
        "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
        "source_name": DIGITALNZ_GAZETTE_SOURCE_NAME,
        "source_tier": DIGITALNZ_GAZETTE_SOURCE_TIER,
        "record_count": len(normalized_records_sorted),
        "page_count": len(page_summaries_sorted),
        "collection_filter": plan["collection_filter"],
        "query_sha256": plan["query_sha256"],
        "text_bearing_count": review["text_bearing_count"],
        "metadata_only_count": review["metadata_only_count"],
        "rights_covered_count": len(normalized_records_sorted) - review["missing_rights_count"],
        "missing_rights_count": review["missing_rights_count"],
        "missing_source_url_count": review["missing_source_url_count"],
        "missing_original_source_url_count": review["missing_original_source_url_count"],
        "missing_landing_url_count": review["missing_landing_url_count"],
        "coverage_warning": review["coverage_warning"],
    }
    coverage["content_sha256"] = sha256_text(_stable_json(coverage))
    coverage["manifest_sha256"] = sha256_text(_stable_json({k: v for k, v in coverage.items() if k != "manifest_sha256"}))

    write_json(validation_path, review)
    write_json(coverage_path, coverage)
    write_json(state_path, {**read_json(state_path, default={}), "validation_ok": review["ok"]})
    return {
        "plan": plan,
        "manifest": manifest,
        "review": review,
        "coverage": coverage,
        "source_records_path": str(source_records_path),
        "records_path": str(records_path),
        "raw_pages_dir": str(raw_pages_dir),
        "state_path": str(state_path),
        "manifest_path": str(manifest_path),
        "validation_path": str(validation_path),
        "coverage_path": str(coverage_path),
        "raw_record_count": len(source_records_sorted),
        "normalized_record_count": len(normalized_records_sorted),
        "page_count": len(page_summaries_sorted),
        "result_count": total_result_count,
        "ok": review["ok"],
    }


def build_digitalnz_gazette_archive(
    source_dir: Path,
    output_dir: Path,
    *,
    year: str,
) -> dict[str, Any]:
    """Bundle a completed DigitalNZ Gazette source export into a signed archive."""
    source_records_path = source_dir / "source_records.jsonl"
    records_path = source_dir / "records.jsonl"
    state_path = source_dir / "_state" / "export_state.json"
    validation_path = source_dir / "manifests" / "validation_report.json"
    manifest_path = source_dir / "manifests" / "latest_manifest.json"
    coverage_path = source_dir / "manifests" / "coverage_report.json"
    required = [
        source_records_path,
        records_path,
        state_path,
        validation_path,
        manifest_path,
        coverage_path,
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "DigitalNZ Gazette archive requires an exported source tree first: "
            + ", ".join(path.as_posix() for path in missing)
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_archive(
        source_dir,
        output_dir,
        year=year,
        archive_name_prefix=DIGITALNZ_GAZETTE_ARCHIVE_PREFIX,
        manifest_name_prefix=DIGITALNZ_GAZETTE_ARCHIVE_PREFIX,
        tar_root_name=DIGITALNZ_GAZETTE_ARCHIVE_PREFIX,
        artifact_class="digitalnz_gazette_source_archive",
        publication_target="source_evidence",
        coverage_statement=(
            "DigitalNZ Gazette source archives are corroborative evidence layers "
            "and remain distinct from official and canonical comparison outputs."
        ),
    )
    archive_manifest_path = output_dir / f"{DIGITALNZ_GAZETTE_ARCHIVE_PREFIX}-{year}.manifest.json"
    archive_manifest = read_json(archive_manifest_path, default={}) or {}
    source_manifest = read_json(manifest_path, default={}) or {}
    release_evidence_path = (
        output_dir / f"{DIGITALNZ_GAZETTE_ARCHIVE_PREFIX}-{year}.release-evidence.json"
    )
    build_release_evidence(
        artifact_class="digitalnz_gazette_source_archive",
        output_path=release_evidence_path,
        subjects=[Path(bundle["archive_path"]), archive_manifest_path, manifest_path],
        manifest=archive_manifest,
        coverage_statement=(
            "DigitalNZ Gazette source archive evidence must remain independent "
            "from canonical comparison outputs and preserve the raw source export."
        ),
        publication_target="source_evidence",
    )
    checksums_path = output_dir / f"{DIGITALNZ_GAZETTE_ARCHIVE_PREFIX}-{year}.SHA256SUMS.txt"
    checksums_path.write_text(
        "\n".join(
            [
                f"{sha256_file(Path(bundle['archive_path']))}  {Path(bundle['archive_path']).name}",
                f"{sha256_file(archive_manifest_path)}  {archive_manifest_path.name}",
                f"{sha256_file(manifest_path)}  {manifest_path.name}",
                f"{sha256_file(release_evidence_path)}  {release_evidence_path.name}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        **bundle,
        "archive_manifest_path": str(archive_manifest_path),
        "source_manifest_path": str(manifest_path),
        "release_evidence_path": str(release_evidence_path),
        "checksums_path": str(checksums_path),
        "archive_manifest_sha256": archive_manifest.get("manifest_sha256"),
        "source_manifest_sha256": source_manifest.get("manifest_sha256"),
        "source_manifest_content_sha256": source_manifest.get("content_sha256"),
    }
