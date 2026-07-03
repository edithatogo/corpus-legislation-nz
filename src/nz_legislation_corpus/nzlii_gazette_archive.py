from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests

from .archive import build_archive
from .artifact_provenance import build_release_evidence
from .utils import (
    read_json,
    read_jsonl,
    sha256_file,
    sha256_text,
    utc_now_iso,
    write_json,
    write_jsonl,
)

NZLII_GAZETTE_SOURCE_ID = "nzlii_gazette"
NZLII_GAZETTE_SOURCE_NAME = "NZLII Gazette redundancy archive"
NZLII_GAZETTE_SOURCE_TIER = "redundancy"
NZLII_GAZETTE_RELEASE_COMMIT = "0000000"
NZLII_GAZETTE_ROBOTS_URL = "https://www.nzlii.org/robots.txt"
NZLII_GAZETTE_SOURCE_URLS = [
    "https://www.nzlii.org/nz/legis/hist_act/",
    "https://www.nzlii.org/nz/legis/num_reg/",
]
NZLII_GAZETTE_ARCHIVE_PREFIX = "corpus-legislation-nz-gazette-nzlii"

_CHALLENGE_MARKERS = ("just a moment", "cloudflare", "managed content", "attention required")
_CONTENT_SIGNAL_RE = re.compile(r"Content-Signal:\s*(.+)", re.IGNORECASE)


def _response_text(response: requests.Response) -> str:
    try:
        return response.text
    except Exception:
        return response.content.decode("utf-8", errors="replace")


def _parse_content_signal(robots_text: str) -> dict[str, str]:
    match = _CONTENT_SIGNAL_RE.search(robots_text)
    if not match:
        return {}
    signals: dict[str, str] = {}
    for part in match.group(1).split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        signals[key.strip()] = value.strip()
    return signals


def _probe_candidate(
    session: requests.Session,
    url: str,
) -> dict[str, Any]:
    response = session.get(url, headers={"User-Agent": "nzlc-nzlii-gazette-probe/1.0"})
    text = _response_text(response)
    lowered = text.lower()
    challenge_detected = any(marker in lowered for marker in _CHALLENGE_MARKERS)
    blocked = response.status_code >= 400 or challenge_detected
    return {
        "url": url,
        "status_code": response.status_code,
        "final_url": str(response.url),
        "content_sha256": sha256_text(text),
        "challenge_detected": challenge_detected,
        "blocked": blocked,
        "content_excerpt": text[:400],
    }


def probe_nzlii_gazette_access(
    *,
    candidate_urls: Sequence[str] | None = None,
    robots_url: str = NZLII_GAZETTE_ROBOTS_URL,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Probe NZLII Gazette access conservatively and record the access state."""
    client = session or requests.Session()
    close_client = session is None
    try:
        robots_response = client.get(robots_url, headers={"User-Agent": "nzlc-nzlii-probe/1.0"})
        robots_text = _response_text(robots_response)
        content_signal = _parse_content_signal(robots_text)
        probes = [_probe_candidate(client, url) for url in candidate_urls or NZLII_GAZETTE_SOURCE_URLS]
    finally:
        if close_client:
            client.close()

    usable_candidates = [probe for probe in probes if not probe["blocked"] and probe["status_code"] < 400]
    if usable_candidates:
        access_status = "usable"
        blocked_reason = ""
    elif any(probe["challenge_detected"] for probe in probes):
        access_status = "blocked"
        blocked_reason = "cloudflare_or_managed_content_challenge"
    elif any(probe["status_code"] in {401, 403, 404, 410, 429} for probe in probes):
        access_status = "blocked"
        blocked_reason = "http_status_block"
    else:
        access_status = "unavailable"
        blocked_reason = "no_usable_candidate_or_allowed_content"

    revisit_criteria = (
        "Revisit only if NZLII publishes an explicitly permitted non-challenge access path "
        "for the Gazette collections and rights review allows bounded collection."
    )
    robots_access_note = (
        "robots.txt advertises content signals for search and reference use, but the live "
        "historical Gazette entry points are currently access-blocked for automated clients."
    )
    return {
        "schema_version": "1.0",
        "source_id": NZLII_GAZETTE_SOURCE_ID,
        "source_name": NZLII_GAZETTE_SOURCE_NAME,
        "source_tier": NZLII_GAZETTE_SOURCE_TIER,
        "generated_at_utc": utc_now_iso(),
        "robots_url": robots_url,
        "robots_accessible": robots_response.status_code < 400,
        "robots_status_code": robots_response.status_code,
        "robots_sha256": sha256_text(robots_text),
        "robots_content_signal": content_signal,
        "robots_access_note": robots_access_note,
        "candidate_urls": list(candidate_urls or NZLII_GAZETTE_SOURCE_URLS),
        "candidate_probes": probes,
        "access_status": access_status,
        "blocked_reason": blocked_reason,
        "revisit_criteria": revisit_criteria,
        "coverage_warning": (
            "NZLII is a secondary corroborating source only. Access is currently blocked "
            "for automated collection, so the track records a blocked source state."
        ),
    }


@dataclass(frozen=True, slots=True)
class NZLIIGazetteArchiveRecord:
    """Source-state or raw archive record for NZLII Gazette material."""

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
        payload.pop("note", None)
        return {key: value for key, value in payload.items() if value is not None}


def _stable_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "stable_id": record["stable_id"],
        "source_id": record.get("source_id", NZLII_GAZETTE_SOURCE_ID),
        "source_name": record.get("source_name", NZLII_GAZETTE_SOURCE_NAME),
        "source_tier": record.get("source_tier", NZLII_GAZETTE_SOURCE_TIER),
        "record_kind": record["record_kind"],
        "source_url": str(record["source_url"]),
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
    }
    return {key: value for key, value in payload.items() if value is not None}


def build_nzlii_gazette_manifest(
    *,
    source_records: Iterable[Mapping[str, Any]],
    probe_result: Mapping[str, Any],
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest for NZLII Gazette source-state records."""
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
            raise ValueError(f"NZLII manifest record is missing required keys: {missing}")
        normalized_records.append(_stable_record_payload(record))

    normalized_records.sort(
        key=lambda item: (
            str(item["record_kind"]),
            str(item["source_url"]),
            str(item["stable_id"]),
        )
    )
    record_kind_counts = Counter(str(record["record_kind"]) for record in normalized_records)
    coverage_state_counts = Counter(str(record["coverage_state"]) for record in normalized_records)
    payload = {
        "schema_version": "1.0",
        "source_id": NZLII_GAZETTE_SOURCE_ID,
        "source_name": NZLII_GAZETTE_SOURCE_NAME,
        "source_tier": NZLII_GAZETTE_SOURCE_TIER,
        "generated_at_utc": utc_now_iso(),
        "record_count": len(normalized_records),
        "record_kind_counts": dict(sorted(record_kind_counts.items())),
        "coverage_state_counts": dict(sorted(coverage_state_counts.items())),
        "probe_result": {
            "access_status": probe_result.get("access_status"),
            "blocked_reason": probe_result.get("blocked_reason"),
            "robots_url": probe_result.get("robots_url"),
            "candidate_urls": probe_result.get("candidate_urls") or [],
            "robots_content_signal": probe_result.get("robots_content_signal") or {},
        },
        "blocked_reason": probe_result.get("blocked_reason") or "",
        "revisit_criteria": probe_result.get("revisit_criteria") or "",
        "robots_url": probe_result.get("robots_url") or NZLII_GAZETTE_ROBOTS_URL,
        "coverage_warning": str(probe_result.get("coverage_warning") or ""),
        "records": normalized_records,
    }
    content_payload = {
        "schema_version": payload["schema_version"],
        "source_id": payload["source_id"],
        "record_count": payload["record_count"],
        "record_kind_counts": payload["record_kind_counts"],
        "coverage_state_counts": payload["coverage_state_counts"],
        "probe_result": payload["probe_result"],
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


def build_nzlii_gazette_review(
    *,
    source_records: Iterable[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    probe_result: Mapping[str, Any],
    source_records_path: Path,
    records_path: Path,
    raw_probe_path: Path,
    state_path: Path,
) -> dict[str, Any]:
    """Review NZLII Gazette source-state evidence."""
    records = list(source_records)
    blocked_count = 0
    missing_rights = 0
    missing_source_url = 0
    missing_hash = 0
    missing_block_reason = 0
    missing_revisit_criteria = 0
    access_status = str(probe_result.get("access_status") or "").strip()
    for record in records:
        if str(record.get("coverage_state") or "") == "blocked":
            blocked_count += 1
        rights_note = str(record.get("rights_note") or "").strip().lower()
        if not rights_note or "nzl" not in rights_note:
            missing_rights += 1
        if not str(record.get("source_url") or "").strip():
            missing_source_url += 1
        if not str(record.get("content_sha256") or "").strip():
            missing_hash += 1
        extraction = record.get("extraction")
        if not isinstance(extraction, dict):
            extraction = {}
        if not str(extraction.get("blocked_reason") or "").strip():
            missing_block_reason += 1
        if not str(extraction.get("revisit_criteria") or "").strip():
            missing_revisit_criteria += 1

    manifest_sha256 = str(manifest.get("manifest_sha256") or "").strip()
    content_sha256 = str(manifest.get("content_sha256") or "").strip()
    ok = (
        access_status in {"blocked", "unavailable", "usable"}
        and bool(blocked_count)
        and not any(
            [
                missing_rights,
                missing_source_url,
                missing_hash,
                missing_block_reason,
                missing_revisit_criteria,
                not manifest_sha256,
                not content_sha256,
            ]
        )
    )
    coverage_warning = str(probe_result.get("coverage_warning") or "")
    if not ok:
        coverage_warning = (
            "NZLII source-state review failed. "
            f"access_status={access_status}, blocked={blocked_count}, rights={missing_rights}, "
            f"source_url={missing_source_url}, hash={missing_hash}, "
            f"blocked_reason={missing_block_reason}, revisit_criteria={missing_revisit_criteria}."
        )
    return {
        "schema_version": "1.0",
        "ok": ok,
        "access_status": access_status,
        "record_count": len(records),
        "blocked_count": blocked_count,
        "missing_rights_count": missing_rights,
        "missing_source_url_count": missing_source_url,
        "missing_hash_count": missing_hash,
        "missing_block_reason_count": missing_block_reason,
        "missing_revisit_criteria_count": missing_revisit_criteria,
        "manifest_sha256": manifest_sha256,
        "content_sha256": content_sha256,
        "source_records_path": str(source_records_path),
        "records_path": str(records_path),
        "raw_probe_path": str(raw_probe_path),
        "state_path": str(state_path),
        "coverage_warning": coverage_warning,
    }


def build_nzlii_gazette_coverage_report(
    *,
    source_records: Iterable[Mapping[str, Any]],
    review: Mapping[str, Any],
    manifest: Mapping[str, Any],
    probe_result: Mapping[str, Any],
) -> dict[str, Any]:
    records = list(source_records)
    coverage = {
        "schema_version": "1.0",
        "source_id": NZLII_GAZETTE_SOURCE_ID,
        "source_name": NZLII_GAZETTE_SOURCE_NAME,
        "source_tier": NZLII_GAZETTE_SOURCE_TIER,
        "record_count": len(records),
        "access_status": probe_result.get("access_status"),
        "blocked_reason": probe_result.get("blocked_reason"),
        "revisit_criteria": probe_result.get("revisit_criteria"),
        "robots_url": probe_result.get("robots_url"),
        "candidate_url_count": len(probe_result.get("candidate_urls") or []),
        "blocked_count": int(review.get("blocked_count") or 0),
        "rights_covered_count": len(records) - int(review.get("missing_rights_count") or 0),
        "missing_rights_count": int(review.get("missing_rights_count") or 0),
        "missing_source_url_count": int(review.get("missing_source_url_count") or 0),
        "missing_hash_count": int(review.get("missing_hash_count") or 0),
        "coverage_warning": str(review.get("coverage_warning") or ""),
        "record_kind_counts": manifest.get("record_kind_counts") or {},
        "coverage_state_counts": manifest.get("coverage_state_counts") or {},
    }
    coverage["content_sha256"] = sha256_text(
        json.dumps(coverage, sort_keys=True, ensure_ascii=False)
    )
    coverage["manifest_sha256"] = sha256_text(
        json.dumps({k: v for k, v in coverage.items() if k != "manifest_sha256"}, sort_keys=True, ensure_ascii=False)
    )
    return coverage


def _blocked_record(
    *,
    probe_result: Mapping[str, Any],
    raw_probe_path: Path,
    source_state_label: str,
) -> NZLIIGazetteArchiveRecord:
    retrieved_at = str(probe_result.get("generated_at_utc") or utc_now_iso())
    content_sha = sha256_file(raw_probe_path)
    blocked_reason = str(probe_result.get("blocked_reason") or "blocked_or_unavailable")
    revisit_criteria = str(probe_result.get("revisit_criteria") or "")
    access_status = str(probe_result.get("access_status") or "blocked")
    rights_note = (
        "NZLII robots.txt advertises search=yes and use=reference, but live "
        "historical Gazette entry points are currently blocked to automated clients."
    )
    return NZLIIGazetteArchiveRecord(
        stable_id=f"gazette-nzlii-{source_state_label}",
        source_id=NZLII_GAZETTE_SOURCE_ID,
        source_name=NZLII_GAZETTE_SOURCE_NAME,
        source_tier=NZLII_GAZETTE_SOURCE_TIER,
        record_kind="blocked_evidence",
        source_url=str(probe_result.get("candidate_urls", [NZLII_GAZETTE_SOURCE_URLS[0]])[0]),
        retrieval_method="http-get",
        retrieved_at=retrieved_at,
        content_sha256=content_sha,
        raw_artifact_path=raw_probe_path.as_posix(),
        rights_note=rights_note,
        source_local_id=source_state_label,
        coverage_state="blocked",
        extraction={
            "access_status": access_status,
            "blocked_reason": blocked_reason,
            "revisit_criteria": revisit_criteria,
            "robots_url": probe_result.get("robots_url"),
            "robots_content_signal": probe_result.get("robots_content_signal") or {},
            "candidate_urls": probe_result.get("candidate_urls") or [],
            "candidate_probes": probe_result.get("candidate_probes") or [],
        },
        http_metadata={
            "robots_accessible": probe_result.get("robots_accessible"),
            "robots_status_code": probe_result.get("robots_status_code"),
        },
        provenance={
            "pipeline_name": "nzlii-gazette",
            "pipeline_version": "1.0.0",
            "source_name": NZLII_GAZETTE_SOURCE_NAME,
            "source_record_id": source_state_label,
            "source_retrieved_at": retrieved_at,
            "release_version": "1.0.0",
            "release_commit": NZLII_GAZETTE_RELEASE_COMMIT,
            "license_note": rights_note,
        },
        note="Blocked source-state evidence for NZLII Gazette redundancy archive.",
    )


def export_nzlii_gazette_source(
    *,
    output_dir: Path,
    candidate_urls: Sequence[str] | None = None,
    robots_url: str = NZLII_GAZETTE_ROBOTS_URL,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Probe NZLII access and write blocked/unavailable source-state evidence."""
    probe_result = probe_nzlii_gazette_access(
        candidate_urls=candidate_urls,
        robots_url=robots_url,
        session=session,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw" / "probe"
    manifests_dir = output_dir / "manifests"
    state_dir = output_dir / "_state"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    raw_probe_path = raw_dir / "source_state.json"
    write_json(raw_probe_path, probe_result)
    record = _blocked_record(
        probe_result=probe_result,
        raw_probe_path=raw_probe_path,
        source_state_label="source-state",
    ).to_dict()
    source_records = [record]
    source_records_path = output_dir / "source_records.jsonl"
    records_path = output_dir / "records.jsonl"
    write_jsonl(source_records_path, source_records)
    write_jsonl(records_path, source_records)

    manifest_path = manifests_dir / "latest_manifest.json"
    validation_path = manifests_dir / "validation_report.json"
    coverage_path = manifests_dir / "coverage_report.json"
    state_path = state_dir / "source_state.json"
    manifest = build_nzlii_gazette_manifest(
        source_records=source_records,
        probe_result=probe_result,
        output_path=manifest_path,
    )
    review = build_nzlii_gazette_review(
        source_records=source_records,
        manifest=manifest,
        probe_result=probe_result,
        source_records_path=source_records_path,
        records_path=records_path,
        raw_probe_path=raw_probe_path,
        state_path=state_path,
    )
    coverage = build_nzlii_gazette_coverage_report(
        source_records=source_records,
        review=review,
        manifest=manifest,
        probe_result=probe_result,
    )
    write_json(validation_path, review)
    write_json(coverage_path, coverage)
    write_json(
        state_path,
        {
            "source_id": NZLII_GAZETTE_SOURCE_ID,
            "access_status": probe_result.get("access_status"),
            "blocked_reason": probe_result.get("blocked_reason"),
            "revisit_criteria": probe_result.get("revisit_criteria"),
            "robots_url": probe_result.get("robots_url"),
            "robots_status_code": probe_result.get("robots_status_code"),
            "robots_content_signal": probe_result.get("robots_content_signal") or {},
            "candidate_urls": probe_result.get("candidate_urls") or [],
            "record_count": len(source_records),
            "validation_ok": review["ok"],
        },
    )
    return {
        "ok": review["ok"],
        "probe_result": probe_result,
        "source_records_path": str(source_records_path),
        "records_path": str(records_path),
        "raw_probe_path": str(raw_probe_path),
        "state_path": str(state_path),
        "manifest_path": str(manifest_path),
        "validation_path": str(validation_path),
        "coverage_path": str(coverage_path),
        "record_count": len(source_records),
        "review": review,
        "manifest": manifest,
        "coverage": coverage,
    }


def build_nzlii_gazette_archive(
    source_dir: Path,
    output_dir: Path,
    *,
    year: str,
) -> dict[str, Any]:
    """Bundle NZLII Gazette source-state or raw archive artifacts."""
    records = read_jsonl(source_dir / "records.jsonl")
    if not records:
        raise RuntimeError(f"No NZLII Gazette source records found in {source_dir / 'records.jsonl'}")
    output_dir.mkdir(parents=True, exist_ok=True)
    source_state = read_json(source_dir / "_state" / "source_state.json", default={}) or {}
    bundle = build_archive(
        source_dir,
        output_dir,
        year=year,
        archive_name_prefix=NZLII_GAZETTE_ARCHIVE_PREFIX,
        manifest_name_prefix=NZLII_GAZETTE_ARCHIVE_PREFIX,
        tar_root_name=NZLII_GAZETTE_ARCHIVE_PREFIX,
        artifact_class="nzlii_gazette_source_archive",
        publication_target="source_evidence",
        coverage_statement=(
            "NZLII Gazette evidence is secondary and rights-caveated; it remains "
            "independent from canonical comparison outputs."
        ),
    )
    manifest_path = output_dir / f"{NZLII_GAZETTE_ARCHIVE_PREFIX}-{year}.nzlii-manifest.json"
    release_path = output_dir / f"{NZLII_GAZETTE_ARCHIVE_PREFIX}-{year}.nzlii-evidence.json"
    build_nzlii_gazette_manifest(
        source_records=records,
        probe_result=source_state,
        output_path=manifest_path,
    )
    source_manifest = read_json(manifest_path, default={}) or {}
    build_release_evidence(
        artifact_class="nzlii_gazette_source_archive",
        output_path=release_path,
        subjects=[Path(bundle["archive_path"]), manifest_path],
        manifest=source_manifest,
        coverage_statement=(
            "NZLII Gazette source archive evidence is secondary and rights-caveated; "
            "it must remain independent from canonical comparison outputs."
        ),
        publication_target="source_evidence",
    )
    checksums_path = output_dir / f"{NZLII_GAZETTE_ARCHIVE_PREFIX}-{year}.SHA256SUMS.txt"
    lines = [
        f"{sha256_file(Path(bundle['archive_path']))}  {Path(bundle['archive_path']).name}",
        f"{sha256_file(Path(bundle['manifest_path']))}  {Path(bundle['manifest_path']).name}",
        f"{sha256_file(Path(bundle['provenance_path']))}  {Path(bundle['provenance_path']).name}",
        f"{sha256_file(manifest_path)}  {manifest_path.name}",
        f"{sha256_file(release_path)}  {release_path.name}",
    ]
    checksums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        **bundle,
        "manifest_path": str(manifest_path),
        "release_evidence_path": str(release_path),
        "checksums_path": str(checksums_path),
    }
