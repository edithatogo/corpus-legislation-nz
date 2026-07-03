from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .digitalnz_gazette import export_digitalnz_gazette_source
from .feed_change import write_feed_change_artifacts
from .utils import read_json, read_jsonl, write_json, write_jsonl

OFFICIAL_GAZETTE_SOURCE_ID = "official_gazette"
DIGITALNZ_GAZETTE_SOURCE_ID = "digitalnz_gazette"
HISTORICAL_GAZETTE_SOURCE_ID = "victoria_lexisnexis_gazette"
NZLII_GAZETTE_SOURCE_ID = "nzlii_gazette"
CANONICAL_TRACK_ID = 46
SOURCE_TRACK_BY_ID = {
    OFFICIAL_GAZETTE_SOURCE_ID: 42,
    DIGITALNZ_GAZETTE_SOURCE_ID: 43,
    HISTORICAL_GAZETTE_SOURCE_ID: 44,
    NZLII_GAZETTE_SOURCE_ID: 45,
}
SOURCE_TIER_BY_ID = {
    OFFICIAL_GAZETTE_SOURCE_ID: "official",
    DIGITALNZ_GAZETTE_SOURCE_ID: "discovery",
    HISTORICAL_GAZETTE_SOURCE_ID: "historical",
    NZLII_GAZETTE_SOURCE_ID: "redundancy",
}
FRESHNESS_STATUS_VALUES = (
    "new",
    "changed",
    "unchanged",
    "duplicate",
    "withdrawn",
    "deleted",
    "blocked",
)


@dataclass(frozen=True, slots=True)
class FreshnessObservation:
    source_id: str
    item_id: str
    source_url: str
    title: str
    content_hash: str
    retrieved_at_utc: str
    source_tier: str
    source_artifact_path: str
    queue_source_track_id: int
    queue_canonical_track_id: int = CANONICAL_TRACK_ID
    blocked_reason: str | None = None
    source_specific_status: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "item_id": self.item_id,
            "source_url": self.source_url,
            "title": self.title,
            "content_hash": self.content_hash,
            "retrieved_at_utc": self.retrieved_at_utc,
            "source_tier": self.source_tier,
            "source_artifact_path": self.source_artifact_path,
            "queue_source_track_id": self.queue_source_track_id,
            "queue_canonical_track_id": self.queue_canonical_track_id,
            "blocked_reason": self.blocked_reason,
            "source_specific_status": self.source_specific_status,
        }


def _source_track_id(source_id: str) -> int | None:
    return SOURCE_TRACK_BY_ID.get(source_id)


def _source_tier(source_id: str) -> str:
    return SOURCE_TIER_BY_ID.get(source_id, "unknown")


def _queue_targets_for_status(source_id: str, status: str) -> list[int]:
    source_track_id = _source_track_id(source_id)
    queue_targets: list[int] = []
    if source_track_id is not None and status in {"new", "changed", "withdrawn", "deleted"}:
        queue_targets.extend([source_track_id, CANONICAL_TRACK_ID])
    elif source_track_id is not None and status in {"blocked", "duplicate"}:
        queue_targets.append(source_track_id)
    return queue_targets


def _read_previous_state(previous_state: Path | None) -> list[dict[str, Any]]:
    if previous_state is None or not previous_state.exists():
        return []
    return read_jsonl(previous_state)


def _load_previous_lookup(previous_state: Path | None) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for record in _read_previous_state(previous_state):
        source_id = str(record.get("source_id") or "").strip()
        item_id = str(record.get("item_id") or "").strip()
        if source_id and item_id:
            lookup[(source_id, item_id)] = record
    return lookup


def _official_observations(
    *,
    official_report: dict[str, Any],
    official_state_path: Path,
) -> list[FreshnessObservation]:
    observations: list[FreshnessObservation] = []
    for row in official_report["state_records"]:
        item_id = str(row["id"])
        observations.append(
            FreshnessObservation(
                source_id=OFFICIAL_GAZETTE_SOURCE_ID,
                item_id=item_id,
                source_url=str(row["url"]),
                title=str(row["title"]),
                content_hash=str(row["content_hash"]),
                retrieved_at_utc=str(row["retrieved_at"]),
                source_tier=_source_tier(OFFICIAL_GAZETTE_SOURCE_ID),
                source_artifact_path=official_state_path.as_posix(),
                queue_source_track_id=SOURCE_TRACK_BY_ID[OFFICIAL_GAZETTE_SOURCE_ID],
                blocked_reason=(
                    "unmapped_official_feed_url" if row["mapping_status"] == "unmapped" else None
                ),
                source_specific_status=str(row["mapping_status"]),
            )
        )
    return observations


def _digitalnz_observations(
    *,
    digitalnz_records_path: Path,
    digitalnz_manifest_path: Path,
    digitalnz_state_path: Path,
) -> list[FreshnessObservation]:
    observations: list[FreshnessObservation] = []
    records = read_jsonl(digitalnz_records_path)
    manifest = read_json(digitalnz_manifest_path, default={}) or {}
    retrieved_at = str(manifest.get("generated_at_utc") or "")
    for row in records:
        item_id = str(row.get("stable_id") or row.get("source_local_id") or "")
        if not item_id:
            continue
        observations.append(
            FreshnessObservation(
                source_id=DIGITALNZ_GAZETTE_SOURCE_ID,
                item_id=item_id,
                source_url=str(row.get("source_url") or row.get("landing_url") or ""),
                title=str(row.get("title") or ""),
                content_hash=str(row.get("content_sha256") or ""),
                retrieved_at_utc=str(row.get("retrieved_at") or retrieved_at),
                source_tier=_source_tier(DIGITALNZ_GAZETTE_SOURCE_ID),
                source_artifact_path=digitalnz_state_path.as_posix(),
                queue_source_track_id=SOURCE_TRACK_BY_ID[DIGITALNZ_GAZETTE_SOURCE_ID],
                blocked_reason=(
                    "missing_rights_or_source_url"
                    if not str(row.get("source_url") or "").strip()
                    or not str(row.get("rights_note") or "").strip()
                    else None
                ),
                source_specific_status=str(row.get("coverage_state") or ""),
            )
        )
    return observations


def _combine_observations(
    observations: list[FreshnessObservation],
    previous_lookup: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    state_records: list[dict[str, Any]] = []
    refresh_queue: list[dict[str, Any]] = []
    review_candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    source_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    queue_counts: Counter[int] = Counter()

    for observation in sorted(observations, key=lambda row: (row.source_id, row.item_id)):
        key = (observation.source_id, observation.item_id)
        if key in seen_keys:
            status = "duplicate"
        else:
            seen_keys.add(key)
            previous = previous_lookup.get(key)
            if observation.blocked_reason:
                status = "blocked"
            elif previous is None:
                status = "new"
            elif str(previous.get("content_hash") or "") != observation.content_hash:
                status = "changed"
            else:
                status = "unchanged"

        previous = previous_lookup.get(key)
        first_seen_at = str(previous.get("first_seen_at_utc") or observation.retrieved_at_utc) if previous else observation.retrieved_at_utc
        last_seen_at = observation.retrieved_at_utc
        record = {
            "schema_version": "1.0",
            "source_id": observation.source_id,
            "source_tier": observation.source_tier,
            "item_id": observation.item_id,
            "source_url": observation.source_url,
            "title": observation.title,
            "content_hash": observation.content_hash,
            "first_seen_at_utc": first_seen_at,
            "last_seen_at_utc": last_seen_at,
            "retrieved_at_utc": observation.retrieved_at_utc,
            "status": status,
            "source_specific_status": observation.source_specific_status,
            "blocked_reason": observation.blocked_reason,
            "source_artifact_path": observation.source_artifact_path,
            "queue_source_track_id": observation.queue_source_track_id,
            "queue_canonical_track_id": observation.queue_canonical_track_id,
        }
        record["queue_targets"] = _queue_targets_for_status(observation.source_id, status)
        record["enqueue_decision"] = (
            "refresh"
            if status in {"new", "changed", "withdrawn", "deleted"}
            else "review"
            if status in {"blocked", "duplicate"}
            else "skip"
        )
        record["reason"] = (
            observation.blocked_reason
            or ("source_item_changed" if status == "changed" else None)
            or ("source_item_withdrawn" if status == "withdrawn" else None)
            or ("source_item_deleted" if status == "deleted" else None)
            or ("duplicate_item" if status == "duplicate" else None)
            or ("source_item_first_seen" if status == "new" else None)
            or ("source_item_unchanged" if status == "unchanged" else None)
        )
        state_records.append(record)
        source_counts[observation.source_id] += 1
        state_counts[status] += 1

        if record["queue_targets"]:
            for target_track_id in record["queue_targets"]:
                queue_record = {
                    "schema_version": "1.0",
                    "target_track_id": target_track_id,
                    "source_id": observation.source_id,
                    "item_id": observation.item_id,
                    "source_url": observation.source_url,
                    "title": observation.title,
                    "status": status,
                    "enqueue_decision": record["enqueue_decision"],
                    "reason": record["reason"],
                    "retrieved_at_utc": observation.retrieved_at_utc,
                    "source_artifact_path": observation.source_artifact_path,
                }
                if queue_record not in refresh_queue:
                    refresh_queue.append(queue_record)
                    queue_counts[target_track_id] += 1

        if record["enqueue_decision"] == "review":
            review_candidates.append(
                {
                    "schema_version": "1.0",
                    "source_id": observation.source_id,
                    "item_id": observation.item_id,
                    "source_url": observation.source_url,
                    "title": observation.title,
                    "status": status,
                    "reason": record["reason"],
                    "retrieved_at_utc": observation.retrieved_at_utc,
                    "source_artifact_path": observation.source_artifact_path,
                }
            )

    current_keys = {(record["source_id"], record["item_id"]) for record in state_records}
    for key, previous in sorted(previous_lookup.items()):
        if key in current_keys:
            continue
        source_id, item_id = key
        source_tier = str(previous.get("source_tier") or _source_tier(source_id))
        missing_status = "deleted" if source_id == DIGITALNZ_GAZETTE_SOURCE_ID else "withdrawn"
        first_seen_at = str(previous.get("first_seen_at_utc") or previous.get("retrieved_at_utc") or "")
        last_seen_at = str(previous.get("last_seen_at_utc") or previous.get("retrieved_at_utc") or "")
        record = {
            "schema_version": "1.0",
            "source_id": source_id,
            "source_tier": source_tier,
            "item_id": item_id,
            "source_url": str(previous.get("source_url") or ""),
            "title": str(previous.get("title") or ""),
            "content_hash": str(previous.get("content_hash") or ""),
            "first_seen_at_utc": first_seen_at,
            "last_seen_at_utc": last_seen_at,
            "retrieved_at_utc": previous.get("retrieved_at_utc") or last_seen_at,
            "status": missing_status,
            "source_specific_status": previous.get("source_specific_status"),
            "blocked_reason": None,
            "source_artifact_path": str(previous.get("source_artifact_path") or ""),
            "queue_source_track_id": _source_track_id(source_id),
            "queue_canonical_track_id": CANONICAL_TRACK_ID,
        }
        record["queue_targets"] = _queue_targets_for_status(source_id, missing_status)
        record["enqueue_decision"] = "refresh"
        record["reason"] = "source_item_missing_from_current_poll"
        state_records.append(record)
        state_counts[missing_status] += 1
        if record["queue_targets"]:
            for target_track_id in record["queue_targets"]:
                queue_record = {
                    "schema_version": "1.0",
                    "target_track_id": target_track_id,
                    "source_id": source_id,
                    "item_id": item_id,
                    "source_url": record["source_url"],
                    "title": record["title"],
                    "status": missing_status,
                    "enqueue_decision": "refresh",
                    "reason": record["reason"],
                    "retrieved_at_utc": record["retrieved_at_utc"],
                    "source_artifact_path": record["source_artifact_path"],
                }
                if queue_record not in refresh_queue:
                    refresh_queue.append(queue_record)
                    queue_counts[target_track_id] += 1
        review_candidates.append(
            {
                "schema_version": "1.0",
                "source_id": source_id,
                "item_id": item_id,
                "source_url": record["source_url"],
                "title": record["title"],
                "status": missing_status,
                "reason": record["reason"],
                "retrieved_at_utc": record["retrieved_at_utc"],
                "source_artifact_path": record["source_artifact_path"],
            }
        )

    state_records.sort(key=lambda row: (row["source_id"], row["item_id"]))
    refresh_queue.sort(key=lambda row: (row["target_track_id"], row["source_id"], row["item_id"]))
    review_candidates.sort(key=lambda row: (row["source_id"], row["item_id"]))

    canonical_queue_count = queue_counts.get(CANONICAL_TRACK_ID, 0)
    return {
        "state_records": state_records,
        "refresh_queue": refresh_queue,
        "review_candidates": review_candidates,
        "state_counts": dict(sorted(state_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "queue_counts": dict(sorted(queue_counts.items())),
        "canonical_queue_count": canonical_queue_count,
        "source_queue_count": sum(
            count for track_id, count in queue_counts.items() if track_id != CANONICAL_TRACK_ID
        ),
    }


def build_gazette_freshness_report(
    *,
    official_feed_path: Path,
    digitalnz_api_key: str | None,
    output_dir: Path,
    official_feed_url: str = "",
    previous_state_path: Path | None = None,
    retrieved_at_utc: str | None = None,
    digitalnz_query_text: str = "Gazette",
    digitalnz_collection_filter: str = "New Zealand Gazette",
    digitalnz_page_size: int = 100,
    digitalnz_start_page: int = 1,
    digitalnz_max_pages: int | None = 1,
    digitalnz_sort_field: str = "date",
    digitalnz_sort_direction: str = "asc",
    digitalnz_api_access_mode: str = "key_required",
    digitalnz_api_url: str = "https://api.digitalnz.org/v3/records.json",
    digitalnz_dnz_repo_root: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    official_dir = output_dir / "official"
    digitalnz_dir = output_dir / "digitalnz"

    official_report = write_feed_change_artifacts(
        official_dir,
        official_feed_path,
        feed_url=official_feed_url,
        retrieved_at=retrieved_at_utc,
        previous_state=read_jsonl(official_dir / "feed_state.jsonl")
        if (official_dir / "feed_state.jsonl").exists()
        else None,
    )
    digitalnz_dir.mkdir(parents=True, exist_ok=True)
    digitalnz_state_path = digitalnz_dir / "_state" / "export_state.json"
    digitalnz_manifest_path = digitalnz_dir / "manifests" / "latest_manifest.json"
    digitalnz_records_path = digitalnz_dir / "records.jsonl"
    if digitalnz_api_key:
        digitalnz_report = export_digitalnz_gazette_source(
            output_dir=digitalnz_dir,
            api_key=digitalnz_api_key,
            query_text=digitalnz_query_text,
            collection_filter=digitalnz_collection_filter,
            page_size=digitalnz_page_size,
            start_page=digitalnz_start_page,
            max_pages=digitalnz_max_pages,
            sort_field=digitalnz_sort_field,
            sort_direction=digitalnz_sort_direction,
            api_access_mode=digitalnz_api_access_mode,
            api_url=digitalnz_api_url,
            dnz_repo_root=digitalnz_dnz_repo_root,
        )
    else:
        digitalnz_dir.joinpath("manifests").mkdir(parents=True, exist_ok=True)
        digitalnz_dir.joinpath("_state").mkdir(parents=True, exist_ok=True)
        write_jsonl(digitalnz_records_path, [])
        write_jsonl(digitalnz_dir / "source_records.jsonl", [])
        write_json(
            digitalnz_manifest_path,
            {
                "schema_version": "1.0",
                "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
                "source_name": "DigitalNZ Gazette discovery/export",
                "source_tier": SOURCE_TIER_BY_ID[DIGITALNZ_GAZETTE_SOURCE_ID],
                "generated_at_utc": official_report["generated_at_utc"],
                "manifest_sha256": "",
                "content_sha256": "",
                "blocked": True,
                "blocked_reason": "digitalnz_api_key_missing",
            },
        )
        write_json(
            digitalnz_state_path,
            {
                "schema_version": "1.0",
                "blocked": True,
                "blocked_reason": "digitalnz_api_key_missing",
                "generated_at_utc": official_report["generated_at_utc"],
            },
        )
        digitalnz_report = {
            "ok": False,
            "blocked": True,
            "blocked_reason": "digitalnz_api_key_missing",
            "records_path": str(digitalnz_records_path),
            "manifest_path": str(digitalnz_manifest_path),
            "state_path": str(digitalnz_state_path),
            "review": {"ok": False, "coverage_warning": "DigitalNZ API key missing"},
        }

    previous_lookup = _load_previous_lookup(previous_state_path)
    observations = _official_observations(
        official_report=official_report,
        official_state_path=official_dir / "feed_state.jsonl",
    )
    observations.extend(
        _digitalnz_observations(
            digitalnz_records_path=Path(digitalnz_report["records_path"]),
            digitalnz_manifest_path=Path(digitalnz_report["manifest_path"]),
            digitalnz_state_path=Path(digitalnz_report["state_path"]),
        )
    )
    if not digitalnz_api_key:
        observations.append(
            FreshnessObservation(
                source_id=DIGITALNZ_GAZETTE_SOURCE_ID,
                item_id="digitalnz-source-blocked",
                source_url="",
                title="DigitalNZ freshness poll blocked",
                content_hash="",
                retrieved_at_utc=official_report["generated_at_utc"],
                source_tier=_source_tier(DIGITALNZ_GAZETTE_SOURCE_ID),
                source_artifact_path=digitalnz_report["state_path"],
                queue_source_track_id=SOURCE_TRACK_BY_ID[DIGITALNZ_GAZETTE_SOURCE_ID],
                blocked_reason="digitalnz_api_key_missing",
                source_specific_status="blocked",
            )
        )
    combined = _combine_observations(observations, previous_lookup)
    combined["schema_version"] = "1.0"
    combined["generated_at_utc"] = official_report["generated_at_utc"]
    combined["official_report"] = official_report
    combined["digitalnz_report"] = digitalnz_report
    combined["feed_url"] = official_feed_url
    combined["item_count"] = len(combined["state_records"])
    combined["coverage_warning"] = (
        "Freshness output is advisory. It records change signals and targeted refresh "
        "queues, but it does not prove corpus completeness."
    )
    combined["source_count"] = len(combined["source_counts"])

    state_path = output_dir / "freshness_state.jsonl"
    queue_path = output_dir / "refresh_queue.jsonl"
    review_candidates_path = output_dir / "review_candidates.jsonl"
    report_path = output_dir / "freshness_report.json"
    source_index_path = output_dir / "source_index.json"

    write_jsonl(state_path, combined["state_records"])
    write_jsonl(queue_path, combined["refresh_queue"])
    write_jsonl(review_candidates_path, combined["review_candidates"])
    write_json(report_path, combined)
    write_json(
        source_index_path,
        {
            "schema_version": "1.0",
            "sources": [
                {
                    "source_id": OFFICIAL_GAZETTE_SOURCE_ID,
                    "source_track_id": SOURCE_TRACK_BY_ID[OFFICIAL_GAZETTE_SOURCE_ID],
                    "source_tier": SOURCE_TIER_BY_ID[OFFICIAL_GAZETTE_SOURCE_ID],
                    "artifact_path": str(official_dir),
                },
                {
                    "source_id": DIGITALNZ_GAZETTE_SOURCE_ID,
                    "source_track_id": SOURCE_TRACK_BY_ID[DIGITALNZ_GAZETTE_SOURCE_ID],
                    "source_tier": SOURCE_TIER_BY_ID[DIGITALNZ_GAZETTE_SOURCE_ID],
                    "artifact_path": str(digitalnz_dir),
                },
                {
                    "source_id": HISTORICAL_GAZETTE_SOURCE_ID,
                    "source_track_id": SOURCE_TRACK_BY_ID[HISTORICAL_GAZETTE_SOURCE_ID],
                    "source_tier": SOURCE_TIER_BY_ID[HISTORICAL_GAZETTE_SOURCE_ID],
                    "artifact_path": "data/victoria-lexisnexis-gazette",
                },
                {
                    "source_id": NZLII_GAZETTE_SOURCE_ID,
                    "source_track_id": SOURCE_TRACK_BY_ID[NZLII_GAZETTE_SOURCE_ID],
                    "source_tier": SOURCE_TIER_BY_ID[NZLII_GAZETTE_SOURCE_ID],
                    "artifact_path": "data/nzlii-gazette",
                },
            ],
            "canonical_track_id": CANONICAL_TRACK_ID,
        },
    )
    return {
        **combined,
        "state_path": str(state_path),
        "queue_path": str(queue_path),
        "review_candidates_path": str(review_candidates_path),
        "report_path": str(report_path),
        "source_index_path": str(source_index_path),
    }
