from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from defusedxml import ElementTree as DET

from .utils import sha256_text

LEGISLATION_HOST_SUFFIX = "legislation.govt.nz"
DEFAULT_REFRESH_REASON = "official_feed_change_detected"
MAPPED_STATUS = "mapped"
MAPPED_WORK_ONLY_STATUS = "mapped_work_only"
UNMAPPED_STATUS = "unmapped"
FEED_SCHEMA_VERSION = "1.0"

_LEGISLATION_TYPES = {
    "act",
    "bill",
    "secondary-legislation",
    "amendment-paper",
}
_FORMAT_SUFFIXES = {".xml", ".html", ".htm", ".pdf"}


@dataclass(frozen=True)
class FeedMapping:
    mapping_status: str
    work_id: str | None = None
    version_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "mapping_status": self.mapping_status,
            "work_id": self.work_id,
            "version_id": self.version_id,
        }


@dataclass(frozen=True)
class FeedItemState:
    id: str
    url: str
    title: str
    updated: str | None
    published: str | None
    content_hash: str
    retrieved_at: str
    mapping_status: str
    work_id: str | None = None
    version_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "updated": self.updated,
            "published": self.published,
            "content_hash": self.content_hash,
            "retrieved_at": self.retrieved_at,
            "mapping_status": self.mapping_status,
            "work_id": self.work_id,
            "version_id": self.version_id,
        }


@dataclass(frozen=True)
class RefreshQueueRecord:
    work_id: str
    version_id: str | None
    source_url: str
    feed_item_id: str
    content_hash: str
    mapping_status: str
    refresh_reason: str = DEFAULT_REFRESH_REASON

    def as_dict(self) -> dict[str, Any]:
        return {
            "work_id": self.work_id,
            "version_id": self.version_id,
            "source_url": self.source_url,
            "feed_item_id": self.feed_item_id,
            "content_hash": self.content_hash,
            "mapping_status": self.mapping_status,
            "refresh_reason": self.refresh_reason,
        }


@dataclass(frozen=True)
class ReviewCandidateRecord:
    feed_item_id: str
    source_url: str
    title: str
    content_hash: str
    retrieved_at: str
    mapping_status: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "feed_item_id": self.feed_item_id,
            "source_url": self.source_url,
            "title": self.title,
            "content_hash": self.content_hash,
            "retrieved_at": self.retrieved_at,
            "mapping_status": self.mapping_status,
            "reason": self.reason,
        }


def _ensure_text(value: bytes | str | Path) -> str:
    if isinstance(value, Path):
        return value.read_text(encoding="utf-8")
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _strip_format_suffix(path: str) -> str:
    lowered = path.lower()
    for suffix in _FORMAT_SUFFIXES:
        if lowered.endswith(suffix):
            return path[: -len(suffix)]
    return path


def _normalize_timestamp(text: str | None) -> str | None:
    if text is None:
        return None
    value = text.strip()
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = f"{value[:-1]}+00:00"
        dt = datetime.fromisoformat(value)
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text_or_empty(element: ET.Element[Any] | None, path: str) -> str:
    if element is None:
        return ""
    text = element.findtext(path)
    return text.strip() if text else ""


def _entry_text(entry: ET.Element[Any], names: list[str]) -> str:
    for name in names:
        text = entry.findtext(name)
        if text and text.strip():
            return text.strip()
    for child in entry:
        tag = child.tag.split("}")[-1]
        if tag in names and child.text and child.text.strip():
            return child.text.strip()
    return ""


def _extract_content(entry: ET.Element[Any]) -> str:
    content_candidates = [
        _entry_text(entry, ["content"]),
        _entry_text(entry, ["encoded"]),
        _entry_text(entry, ["summary"]),
        _entry_text(entry, ["description"]),
    ]
    if any(content_candidates):
        return "\n".join(part for part in content_candidates if part)
    return ""


def _item_source_text(
    item_id: str, url: str, title: str, updated: str | None, published: str | None, content: str
) -> str:
    return "\n".join(
        [
            item_id,
            url,
            title,
            updated or "",
            published or "",
            content,
        ]
    )


def _split_legislation_path(url: str) -> list[str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not host.endswith(LEGISLATION_HOST_SUFFIX):
        return []
    path = _strip_format_suffix(parsed.path.strip("/"))
    parts = [part for part in path.split("/") if part]
    if len(parts) < 4:
        return []
    head = parts[0].lower()
    if head not in _LEGISLATION_TYPES:
        return []
    return parts


def map_feed_url(url: str) -> FeedMapping:
    parts = _split_legislation_path(url)
    if not parts:
        return FeedMapping(mapping_status=UNMAPPED_STATUS)
    work_parts = parts[:4]
    if len(parts) >= 6:
        if parts[5].lower() == "latest":
            return FeedMapping(
                mapping_status=MAPPED_WORK_ONLY_STATUS,
                work_id="_".join(work_parts),
                version_id=None,
            )
        return FeedMapping(
            mapping_status=MAPPED_STATUS,
            work_id="_".join(work_parts),
            version_id="_".join(parts[:6]),
        )
    return FeedMapping(
        mapping_status=MAPPED_WORK_ONLY_STATUS,
        work_id="_".join(work_parts),
        version_id=None,
    )


def _parse_rss_items(root: ET.Element[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        title = _text_or_empty(item, "title")
        url = _text_or_empty(item, "link") or _text_or_empty(item, "guid")
        item_id = _text_or_empty(item, "guid") or url or title
        updated = _normalize_timestamp(_text_or_empty(item, "updated"))
        published = _normalize_timestamp(_text_or_empty(item, "pubDate"))
        content = _extract_content(item) or _text_or_empty(item, "description")
        items.append(
            {
                "id": item_id,
                "url": url,
                "title": title,
                "updated": updated,
                "published": published,
                "content": content,
            }
        )
    return items


def _parse_atom_items(root: ET.Element[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in root.findall(".//{*}entry"):
        title = _entry_text(entry, ["title"])
        links = entry.findall("{*}link")
        url = ""
        for link in links:
            rel = str(link.attrib.get("rel") or "alternate").lower()
            href = str(link.attrib.get("href") or "")
            if rel in {"alternate", "self"} and href:
                url = href
                if rel == "alternate":
                    break
        item_id = _entry_text(entry, ["id"]) or url or title
        updated = _normalize_timestamp(_entry_text(entry, ["updated"]))
        published = _normalize_timestamp(_entry_text(entry, ["published"]))
        content = _extract_content(entry)
        if not content:
            content = _entry_text(entry, ["summary"])
        items.append(
            {
                "id": item_id,
                "url": url,
                "title": title,
                "updated": updated,
                "published": published,
                "content": content,
            }
        )
    return items


def parse_feed_items(feed_xml: bytes | str | Path) -> list[dict[str, Any]]:
    root = DET.fromstring(_ensure_text(feed_xml))
    tag = root.tag.split("}")[-1].lower()
    if tag == "rss":
        return _parse_rss_items(root)
    if tag == "feed":
        return _parse_atom_items(root)
    raise ValueError(f"Unsupported feed root element: {root.tag}")


def _current_timestamp(retrieved_at: str | None) -> str:
    if retrieved_at:
        normalized = _normalize_timestamp(retrieved_at)
        if normalized:
            return normalized
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _state_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(record.get("published") or record.get("updated") or ""),
        str(record.get("title") or ""),
        str(record.get("id") or ""),
    )


def _state_lookup(previous_state: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for record in previous_state or []:
        feed_item_id = str(record.get("id") or "").strip()
        if feed_item_id:
            lookup[feed_item_id] = record
    return lookup


def build_feed_change_detection(
    feed_xml: bytes | str | Path,
    *,
    feed_url: str = "",
    retrieved_at: str | None = None,
    previous_state: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    parsed_items = parse_feed_items(feed_xml)
    now = _current_timestamp(retrieved_at)
    previous_by_id = _state_lookup(previous_state)

    state_records: list[dict[str, Any]] = []
    refresh_queue: list[dict[str, Any]] = []
    review_candidates: list[dict[str, Any]] = []
    seen_refresh_keys: set[tuple[str, str | None, str]] = set()
    seen_review_keys: set[str] = set()

    seen_feed_ids: set[str] = set()
    parsed_items = sorted(parsed_items, key=_state_key)
    for item in parsed_items:
        mapping = map_feed_url(str(item["url"]))
        feed_item_id = str(item["id"])
        if feed_item_id in seen_feed_ids:
            continue
        seen_feed_ids.add(feed_item_id)
        content_hash = sha256_text(
            _item_source_text(
                feed_item_id,
                str(item["url"]),
                str(item["title"]),
                item["updated"],
                item["published"],
                str(item["content"]),
            )
        )
        state = FeedItemState(
            id=feed_item_id,
            url=str(item["url"]),
            title=str(item["title"]),
            updated=item["updated"],
            published=item["published"],
            content_hash=content_hash,
            retrieved_at=now,
            mapping_status=mapping.mapping_status,
            work_id=mapping.work_id,
            version_id=mapping.version_id,
        ).as_dict()
        state_records.append(state)

        previous = previous_by_id.get(state["id"])
        changed = previous is None or str(previous.get("content_hash") or "") != content_hash
        if mapping.mapping_status == UNMAPPED_STATUS:
            if state["id"] not in seen_review_keys:
                review_candidates.append(
                    ReviewCandidateRecord(
                        feed_item_id=state["id"],
                        source_url=state["url"],
                        title=state["title"],
                        content_hash=content_hash,
                        retrieved_at=now,
                        mapping_status=mapping.mapping_status,
                        reason="could_not_map_legislation_url",
                    ).as_dict()
                )
                seen_review_keys.add(state["id"])
            continue

        refresh_key = (state["work_id"] or state["id"], state["version_id"], state["url"])
        if not changed and previous is not None:
            continue
        if refresh_key in seen_refresh_keys:
            continue
        seen_refresh_keys.add(refresh_key)
        refresh_queue.append(
            RefreshQueueRecord(
                work_id=str(state["work_id"] or state["id"]),
                version_id=state["version_id"],
                source_url=state["url"],
                feed_item_id=state["id"],
                content_hash=content_hash,
                mapping_status=mapping.mapping_status,
            ).as_dict()
        )

    state_records.sort(key=_state_key)
    refresh_queue.sort(
        key=lambda record: (
            str(record["work_id"]),
            str(record["version_id"] or ""),
            str(record["feed_item_id"]),
        )
    )
    review_candidates.sort(
        key=lambda record: (str(record["feed_item_id"]), str(record["source_url"]))
    )

    return {
        "schema_version": FEED_SCHEMA_VERSION,
        "generated_at_utc": now,
        "feed_url": feed_url,
        "item_count": len(state_records),
        "mapped_item_count": sum(
            1 for record in state_records if record["mapping_status"] != UNMAPPED_STATUS
        ),
        "unmapped_item_count": sum(
            1 for record in state_records if record["mapping_status"] == UNMAPPED_STATUS
        ),
        "state_records": state_records,
        "refresh_queue": refresh_queue,
        "review_candidates": review_candidates,
        "coverage_warning": (
            "Feed change detection is advisory. It records freshness signals and "
            "targeted refresh candidates, but it does not prove full corpus coverage."
        ),
    }


def write_feed_change_artifacts(
    output_dir: Path,
    feed_xml: bytes | str | Path,
    *,
    feed_url: str = "",
    retrieved_at: str | None = None,
    previous_state: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    report = build_feed_change_detection(
        feed_xml,
        feed_url=feed_url,
        retrieved_at=retrieved_at,
        previous_state=previous_state,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "feed_state.jsonl").write_text(
        "".join(
            f"{json.dumps(row, sort_keys=True, ensure_ascii=False)}\n"
            for row in report["state_records"]
        ),
        encoding="utf-8",
    )
    (output_dir / "refresh_queue.jsonl").write_text(
        "".join(
            f"{json.dumps(row, sort_keys=True, ensure_ascii=False)}\n"
            for row in report["refresh_queue"]
        ),
        encoding="utf-8",
    )
    (output_dir / "review_candidates.jsonl").write_text(
        "".join(
            f"{json.dumps(row, sort_keys=True, ensure_ascii=False)}\n"
            for row in report["review_candidates"]
        ),
        encoding="utf-8",
    )
    (output_dir / "feed_change_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report
