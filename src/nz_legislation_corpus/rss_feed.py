from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .utils import read_json, read_jsonl

FEED_FILENAME = "feed.xml"
FEED_TITLE = "New Zealand Legislation Corpus - Recent Changes"
FEED_DESCRIPTION = (
    "Recent additions and updates to the New Zealand Legislation Corpus. "
    "Tracking acts, bills, secondary legislation, and amendment papers "
    "synced from the official NZ Legislation API."
)
FEED_LINK = "https://huggingface.co/datasets/edithatogo/corpus-legislation-nz"
FEED_LANGUAGE = "en-nz"

_TYPE_LABELS: dict[str, str] = {
    "act": "Act",
    "bill": "Bill",
    "secondary_legislation": "Secondary Legislation",
    "amendment_paper": "Amendment Paper",
}


def _legislation_url(record: dict[str, Any]) -> str:
    xml_url = str(record.get("xml_url") or "")
    html_url = str(record.get("html_url") or "")
    return html_url or xml_url or FEED_LINK


def _rfc2822(dt: datetime) -> str:
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    month = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ][dt.month - 1]
    return f"{weekday}, {dt.day:02d} {month} {dt.year:04d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} GMT"


def _add_text(parent: ET.Element[Any], tag: str, text: str) -> None:
    elem = ET.SubElement(parent, tag)
    elem.text = text


def build_feed(
    records_path: Path,
    changes_path: Path,
    output_path: Path,
    *,
    feed_title: str = FEED_TITLE,
    feed_description: str = FEED_DESCRIPTION,
    feed_link: str = FEED_LINK,
    max_items: int = 50,
) -> dict[str, Any]:
    records = read_jsonl(records_path)
    records_by_id: dict[str, dict[str, Any]] = {}
    for r in records:
        sid = str(r.get("stable_id") or "")
        if sid:
            records_by_id[sid] = r

    changes = read_json(changes_path, default={})
    added_ids: list[str] = changes.get("added", [])
    changed_ids: list[str] = changes.get("changed", [])
    generated_at = changes.get("generated_at_utc", "")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for sid in added_ids + changed_ids:
        if sid in seen:
            continue
        seen.add(sid)
        record = records_by_id.get(sid, {})
        title = str(record.get("title") or sid)
        leg_type = str(record.get("legislation_type") or "")
        type_label = _TYPE_LABELS.get(leg_type, leg_type.replace("_", " ").title())
        year = str(record.get("year") or "")

        item_title = f"{title} ({type_label})" if not year else f"{title} - {year} ({type_label})"
        link = _legislation_url(record)

        desc_parts: list[str] = []
        if sid in added_ids:
            desc_parts.append("Added to corpus")
        if sid in changed_ids:
            desc_parts.append("Updated")
        status = str(record.get("legislation_status") or "")
        if status:
            desc_parts.append(f"Status: {status.replace('_', ' ').title()}")
        description = " - ".join(desc_parts) if desc_parts else ""

        items.append(
            {
                "title": item_title,
                "link": link,
                "pub_date": generated_at,
                "description": description,
                "category": type_label,
                "stable_id": sid,
            }
        )
        if len(items) >= max_items:
            break

    rss = ET.Element("rss", attrib={"version": "2.0", "xmlns:atom": "http://www.w3.org/2005/Atom"})
    channel = ET.SubElement(rss, "channel")

    _add_text(channel, "title", feed_title)
    _add_text(channel, "link", feed_link)
    _add_text(channel, "description", feed_description)
    _add_text(channel, "language", FEED_LANGUAGE)
    _add_text(channel, "generator", "nzlc rss-feed")

    atom_self = ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
    atom_self.set("href", f"{feed_link}/resolve/main/{FEED_FILENAME}")
    atom_self.set("rel", "self")
    atom_self.set("type", "application/rss+xml")

    if generated_at:
        _add_text(channel, "pubDate", generated_at.replace("+00:00", "GMT").replace("Z", "GMT"))
    _add_text(channel, "lastBuildDate", datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"))

    for item in items:
        elem = ET.SubElement(channel, "item")
        _add_text(elem, "title", item["title"])
        _add_text(elem, "link", item["link"])
        _add_text(elem, "guid", item["stable_id"])
        if item["pub_date"]:
            _add_text(
                elem, "pubDate", item["pub_date"].replace("+00:00", "GMT").replace("Z", "GMT")
            )
        _add_text(elem, "description", item["description"])
        _add_text(elem, "category", item["category"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(rss)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    return {
        "ok": True,
        "item_count": len(items),
        "output_path": str(output_path),
    }
