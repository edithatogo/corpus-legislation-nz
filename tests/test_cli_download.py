from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pytest
import requests

from nz_legislation_corpus.cli import _download_first_available_format
from nz_legislation_corpus.config import Settings
from nz_legislation_corpus.nz_api import NZLegislationClient


@dataclass
class FakeResponse:
    status_code: int
    payload: object | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    content: bytes = b""
    text: str = ""

    def json(self) -> object:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append((method, url))
        return self.responses.pop(0)

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self.request("GET", url, **kwargs)


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = dict(
        nz_api_key="secret",
        nz_api_base_url="https://api.example.invalid/v0",
        output_dir=Path("data"),
        search_terms=["act"],
        search_field="title",
        search_sort_by="most_recently_updated",
        legislation_types=[],
        legislation_status=None,
        publisher=None,
        per_page=100,
        request_timeout_seconds=30.0,
        min_seconds_between_requests=0.2,
        max_retries=5,
        rate_limit_low_watermark=10,
        rate_limit_reset_padding_seconds=2.0,
        rate_limit_max_sleep_seconds=60.0,
        hf_token=None,
        hf_repo_id=None,
        hf_revision="main",
        zenodo_token=None,
        zenodo_api_url="https://sandbox.zenodo.org/api",
        zenodo_deposition_id=None,
        archive_title="New Zealand Legislation Corpus",
        archive_creators=[],
        archive_license="cc-by-4.0",
        archive_publish_default=False,
        pipeline_version="test",
    )
    values.update(overrides)
    return Settings(**cast("Any", values))


def _make_version(xml_url: str | None = None, html_url: str | None = None) -> dict[str, Any]:
    version: dict[str, Any] = {
        "title": "Test Act",
        "version_id": "test-act-2026/latest",
        "work_id": "test-act-2026",
    }
    formats: list[dict[str, str]] = []
    if xml_url:
        formats.append({"type": "xml", "url": xml_url})
    if html_url:
        formats.append({"type": "html", "url": html_url})
    if formats:
        version["formats"] = formats
    return version


@pytest.mark.unit
def test_download_xml_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession([FakeResponse(status_code=200, content=b"<xml/>")])
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.0), session=session)
    version = _make_version(xml_url="https://example.invalid/file.xml")

    raw_content, url, content_type, warnings = _download_first_available_format(client, version)

    assert raw_content == b"<xml/>"
    assert url == "https://example.invalid/file.xml"
    assert content_type == "application/xml"
    assert warnings == []


@pytest.mark.unit
def test_download_xml_fails_html_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(status_code=404, content=b""),
            FakeResponse(status_code=200, content=b"<html/>"),
        ]
    )
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.0), session=session)
    version = _make_version(
        xml_url="https://example.invalid/file.xml",
        html_url="https://example.invalid/file.html",
    )

    raw_content, url, content_type, warnings = _download_first_available_format(client, version)

    assert raw_content == b"<html/>"
    assert url == "https://example.invalid/file.html"
    assert content_type == "text/html"
    assert len(warnings) == 1
    assert "XML download failed" in warnings[0]
    assert "used HTML" in warnings[0]


@pytest.mark.unit
def test_download_both_fail_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Use max_retries=1 so that HTTP 500 in download_url is not retried
    session = FakeSession(
        [
            FakeResponse(status_code=404, content=b""),
            FakeResponse(status_code=500, content=b""),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=1), session=session
    )
    version = _make_version(
        xml_url="https://example.invalid/file.xml",
        html_url="https://example.invalid/file.html",
    )

    with pytest.raises(requests.HTTPError):
        _download_first_available_format(client, version)


@pytest.mark.unit
def test_download_html_only(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession([FakeResponse(status_code=200, content=b"<html/>")])
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.0), session=session)
    version = _make_version(html_url="https://example.invalid/file.html")

    raw_content, url, content_type, warnings = _download_first_available_format(client, version)

    assert raw_content == b"<html/>"
    assert url == "https://example.invalid/file.html"
    assert content_type == "text/html"
    assert warnings == []


@pytest.mark.unit
def test_download_uses_alternate_dated_html_suffix() -> None:
    session = FakeSession(
        [
            FakeResponse(status_code=404, content=b""),
            FakeResponse(status_code=200, content=b"<html/>"),
        ]
    )
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.0), session=session)
    version = _make_version(html_url="https://example.invalid/1992-04-10/")

    raw_content, url, content_type, warnings = _download_first_available_format(client, version)

    assert raw_content == b"<html/>"
    assert url == "https://example.invalid/1992-04-10A/"
    assert content_type == "text/html"
    assert "Used alternate dated URL" in warnings[0]


@pytest.mark.unit
def test_download_neither_available() -> None:
    session = FakeSession([])
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.0), session=session)
    version = _make_version()

    raw_content, url, content_type, warnings = _download_first_available_format(client, version)

    assert raw_content == b""
    assert url is None
    assert content_type is None
    assert warnings == []
