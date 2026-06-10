from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from .extract_text import extract_text_best_effort
from .schema import RECORD_SCHEMA_VERSION
from .utils import sha256_bytes, sha256_text


def _format_url(version: dict[str, Any], fmt: str) -> str | None:
    for item in version.get("formats", []) or []:
        if str(item.get("type", "")).lower() == fmt.lower():
            return item.get("url")
    return None


def _derive_year(version: dict[str, Any]) -> int | None:
    candidates = [
        version.get("version_date"),
        version.get("date"),
        version.get("as_at_date"),
        version.get("publication_date"),
        version.get("version_id"),
        version.get("work_id"),
        version.get("title"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        match = re.search(r"(18|19|20)\d{2}", str(candidate))
        if match:
            return int(match.group(0))
    return None


def normalize_version_record(
    version: dict[str, Any],
    *,
    raw_content: bytes | None = None,
    raw_content_url: str | None = None,
    raw_content_type: str | None = None,
    pipeline_version: str = "local-dev",
) -> dict[str, Any]:
    version_json = json.dumps(version, sort_keys=True, ensure_ascii=False).encode("utf-8")
    text = ""
    if raw_content:
        text = extract_text_best_effort(raw_content, raw_content_type, raw_content_url)

    version_id = str(version.get("version_id") or "")
    work_id = str(version.get("work_id") or "")
    stable_id = version_id or work_id or sha256_bytes(version_json)
    legislation_type = str(version.get("legislation_type") or "unknown").lower().replace(" ", "_")
    year = _derive_year(version)
    xml_url = _format_url(version, "xml")
    html_url = _format_url(version, "html")
    pdf_url = _format_url(version, "pdf")

    raw_sha = sha256_bytes(raw_content) if raw_content else ""
    id_parts = f"{work_id} {version_id}"
    id_is_ephemeral = "~" in id_parts
    id_ephemeral_reason = (
        "contains ~ segment per NZ Legislation API identifier rules" if id_is_ephemeral else ""
    )
    now = datetime.now(UTC).replace(microsecond=0)
    record = {
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "stable_id": stable_id,
        "work_id": work_id,
        "version_id": version_id,
        "title": version.get("title") or "",
        "jurisdiction": "New Zealand",
        "country": "NZ",
        "source": "New Zealand Legislation API",
        "source_url": html_url or xml_url or pdf_url or raw_content_url or "",
        "api_url": f"https://api.legislation.govt.nz/v0/versions/{version_id}/"
        if version_id
        else "",
        "xml_url": xml_url or "",
        "html_url": html_url or "",
        "pdf_url": pdf_url or "",
        "legislation_type": legislation_type,
        "legislation_subtype": version.get("act_type")
        or version.get("bill_type")
        or version.get("instrument_type_group")
        or "",
        "legislation_status": version.get("legislation_status")
        or version.get("act_status")
        or version.get("bill_status")
        or version.get("instrument_status")
        or "",
        "version_date": version.get("version_date") or version.get("date") or "",
        "year": year,
        "scrape_date": now.date().isoformat(),
        "ingest_timestamp_utc": now.isoformat(),
        "administering_agencies": version.get("administering_agencies") or [],
        "is_latest_version": bool(version.get("is_latest_version", False)),
        "language": "en",
        "text": text,
        "raw_xml_sha256": raw_sha
        if (raw_content_url or "").lower().endswith(".xml/")
        or "xml" in (raw_content_type or "").lower()
        else "",
        "raw_content_sha256": raw_sha,
        "text_sha256": sha256_text(text),
        "source_hash": sha256_bytes(raw_content or version_json),
        "pipeline_version": pipeline_version,
        "id_is_ephemeral": id_is_ephemeral,
        "id_ephemeral_reason": id_ephemeral_reason,
        "raw_version_metadata": version,
    }
    return record
