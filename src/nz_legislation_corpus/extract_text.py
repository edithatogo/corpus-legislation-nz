from __future__ import annotations

import re
from collections.abc import Iterable
from html import unescape

from defusedxml import ElementTree as DET


def _flatten_text(parts: Iterable[str]) -> str:
    text = " ".join(part.strip() for part in parts if part and part.strip())
    text = re.sub(r"\s+", " ", text)
    # Keep basic section readability around common markers.
    text = re.sub(r"\s+([,.;:)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    return text.strip()


def extract_text_from_xml(xml_bytes: bytes) -> str:
    """Extract human-readable text from NZ legislation XML.

    This keeps the extractor intentionally conservative: preserve all textual content rather
    than trying to infer legal structure too early. A downstream structural extractor can be
    added once the corpus is stable.
    """
    if not xml_bytes:
        return ""
    root = DET.fromstring(xml_bytes)
    return _flatten_text(root.itertext())


def extract_text_from_html(html_bytes: bytes) -> str:
    raw = html_bytes.decode("utf-8", errors="replace")
    raw = re.sub(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", " ", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>", " ", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return _flatten_text([unescape(raw)])


def extract_text_best_effort(
    content: bytes, content_type: str | None = None, url: str | None = None
) -> str:
    marker = " ".join(part for part in [content_type or "", url or ""]).lower()
    if "xml" in marker:
        try:
            return extract_text_from_xml(content)
        except Exception:
            pass
    if "html" in marker or content.lstrip().startswith(b"<html"):
        return extract_text_from_html(content)
    try:
        return extract_text_from_xml(content)
    except Exception:
        return extract_text_from_html(content)
