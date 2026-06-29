from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pytest
import requests

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
    def __init__(self, responses: list[FakeResponse | requests.RequestException]):
        self.responses = list(responses)
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append((method, url))
        response = self.responses.pop(0)
        if isinstance(response, requests.RequestException):
            raise response
        return response

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


@pytest.mark.unit
def test_request_json_respects_minimum_spacing(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession([FakeResponse(status_code=200, payload={"ok": True})])
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.5), session=session)
    client.last_request_at = 10.0
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 10.2)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)

    client.request_json("GET", "works/")

    assert sleeps == [pytest.approx(0.3)]


@pytest.mark.unit
def test_request_json_retries_on_429_with_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(
                status_code=429, payload={"error": "throttle"}, headers={"Retry-After": "7"}
            ),
            FakeResponse(status_code=200, payload={"ok": True}),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)

    response = client.request_json("GET", "works/")

    assert response.data == {"ok": True}
    assert sleeps == [7.0]
    assert session.requests == [
        ("GET", "https://api.example.invalid/v0/works/"),
        ("GET", "https://api.example.invalid/v0/works/"),
    ]


@pytest.mark.unit
def test_request_json_retries_on_transient_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(
        [
            requests.ReadTimeout("slow upstream"),
            FakeResponse(status_code=200, payload={"ok": True}),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.random.random", lambda: 0.0)

    response = client.request_json("GET", "works/")

    assert response.data == {"ok": True}
    assert sleeps == [2.0]
    assert session.requests == [
        ("GET", "https://api.example.invalid/v0/works/"),
        ("GET", "https://api.example.invalid/v0/works/"),
    ]


@pytest.mark.unit
def test_request_json_retries_on_403_with_jittered_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(status_code=403, payload={"error": "burst"}),
            FakeResponse(status_code=200, payload={"ok": True}),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.random.random", lambda: 0.0)

    response = client.request_json("GET", "works/")

    assert response.data == {"ok": True}
    assert sleeps == [30.0]


@pytest.mark.unit
def test_request_json_pauses_when_quota_is_low(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(
                status_code=200,
                payload={"ok": True},
                headers={"X-RateLimit-Remaining": "2", "X-RateLimit-Reset": "1004"},
            )
        ]
    )
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.0), session=session)
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.time", lambda: 1000.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)

    response = client.request_json("GET", "works/")

    assert response.data == {"ok": True}
    assert sleeps == [2.0]


@pytest.mark.unit
def test_sleep_for_low_quota_capped_at_max(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(
                status_code=200,
                payload={"ok": True},
                headers={
                    "X-RateLimit-Remaining": "1",
                    "X-RateLimit-Reset": "10000",
                },
            )
        ],
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, rate_limit_max_sleep_seconds=5.0),
        session=session,
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.time", lambda: 1000.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)

    response = client.request_json("GET", "works/")

    assert response.data == {"ok": True}
    # With remaining=1, reset=10000 (9000s in the future), raw sleep would be
    # max(2.0, 9000/1) = 9000s, but capped at rate_limit_max_sleep_seconds=5.0
    assert sleeps == [pytest.approx(5.0)]


@pytest.mark.unit
def test_discover_versions_honors_max_works() -> None:
    client = NZLegislationClient(make_settings(search_terms=["acts"]), session=FakeSession([]))
    works = [{"work_id": str(index), "title": f"Work {index}"} for index in range(1, 11)]
    seen_work_ids: list[str] = []

    client.iter_search_works = lambda **kwargs: iter(works)  # ty: ignore[invalid-assignment]

    def fake_iter_work_versions(work_id: str, *, sort: str = "desc") -> Iterator[dict[str, str]]:
        seen_work_ids.append(work_id)
        return iter([{"version_id": f"{work_id}-v1", "work_id": work_id}])

    client.iter_work_versions = fake_iter_work_versions  # ty: ignore[invalid-assignment]

    versions = list(
        client.discover_versions(search_terms=["acts"], search_field="title", max_works=5)
    )

    assert [version["work_id"] for version in versions] == ["1", "2", "3", "4", "5"]
    assert seen_work_ids == ["1", "2", "3", "4", "5"]


@pytest.mark.unit
def test_discover_versions_honors_max_works_for_seed_ids() -> None:
    client = NZLegislationClient(make_settings(search_terms=["acts"]), session=FakeSession([]))
    seed_ids = [f"seed-{index}" for index in range(1, 8)]
    seen_work_ids: list[str] = []

    client.iter_search_works = lambda **kwargs: iter([{"work_id": "search-1", "title": "Search"}])  # ty: ignore[invalid-assignment]

    def fake_iter_work_versions(work_id: str, *, sort: str = "desc") -> Iterator[dict[str, str]]:
        seen_work_ids.append(work_id)
        return iter([{"version_id": f"{work_id}-v1", "work_id": work_id}])

    client.iter_work_versions = fake_iter_work_versions  # ty: ignore[invalid-assignment]

    versions = list(
        client.discover_versions(
            search_terms=["acts"],
            search_field="title",
            seed_work_ids=seed_ids,
            max_works=5,
        )
    )

    assert [version["work_id"] for version in versions] == seed_ids[:5]
    assert seen_work_ids == seed_ids[:5]


@pytest.mark.unit
def test_retry_after_seconds_invalid_header_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    client = NZLegislationClient(make_settings(), session=FakeSession([]))
    monkeypatch.setattr("nz_legislation_corpus.nz_api.random.random", lambda: 0.0)

    response = FakeResponse(status_code=429, headers={"Retry-After": "not-a-number"})
    seconds = client._retry_after_seconds(response, fallback_attempt=1)
    assert seconds == 2.0


@pytest.mark.unit
def test_download_url_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(
                status_code=429, payload={"error": "throttle"}, headers={"Retry-After": "5"}
            ),
            FakeResponse(status_code=200, content=b"ok"),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)

    content = client.download_url("https://example.invalid/file.xml")

    assert content == b"ok"
    assert sleeps == [5.0]
    assert len(session.requests) == 2


@pytest.mark.unit
def test_download_url_retries_on_403(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(status_code=403, payload={"error": "burst"}),
            FakeResponse(status_code=200, content=b"ok"),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.random.random", lambda: 0.0)

    content = client.download_url("https://example.invalid/file.xml")

    assert content == b"ok"
    assert sleeps == [30.0]


@pytest.mark.unit
def test_download_url_retries_on_transient_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(
        [
            requests.ReadTimeout("slow upstream"),
            FakeResponse(status_code=200, content=b"ok"),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.random.random", lambda: 0.0)

    content = client.download_url("https://example.invalid/file.xml")

    assert content == b"ok"
    assert sleeps == [2.0]
    assert len(session.requests) == 2


@pytest.mark.unit
def test_download_url_pauses_when_quota_is_low(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(
                status_code=200,
                content=b"ok",
                headers={"X-RateLimit-Remaining": "2", "X-RateLimit-Reset": "1004"},
            )
        ]
    )
    client = NZLegislationClient(make_settings(min_seconds_between_requests=0.0), session=session)
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.time", lambda: 1000.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)

    content = client.download_url("https://example.invalid/file.xml")

    assert content == b"ok"
    # remaining=2, reset=1004, now=1000 -> wait_until_reset=4, sleep_seconds=max(2.0, 4/2)=2.0
    assert sleeps == [2.0]


@pytest.mark.unit
def test_sleep_for_low_quota_missing_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    client = NZLegislationClient(make_settings(), session=FakeSession([]))
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)

    client._sleep_for_low_quota({})
    client._sleep_for_low_quota({"X-RateLimit-Remaining": "10"})
    client._sleep_for_low_quota({"X-RateLimit-Reset": "100"})

    assert sleeps == []


@pytest.mark.unit
def test_sleep_for_low_quota_reset_already_past(monkeypatch: pytest.MonkeyPatch) -> None:
    client = NZLegislationClient(make_settings(), session=FakeSession([]))
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.time", lambda: 2000.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)

    client._sleep_for_low_quota({"X-RateLimit-Remaining": "1", "X-RateLimit-Reset": "1000"})
    assert sleeps == []


@pytest.mark.unit
def test_sleep_for_low_quota_above_watermark(monkeypatch: pytest.MonkeyPatch) -> None:
    client = NZLegislationClient(make_settings(rate_limit_low_watermark=5), session=FakeSession([]))
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)

    client._sleep_for_low_quota({"X-RateLimit-Remaining": "10", "X-RateLimit-Reset": "2000"})
    assert sleeps == []


@pytest.mark.unit
def test_download_url_raises_after_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(status_code=429, headers={"Retry-After": "1"}),
            FakeResponse(status_code=429, headers={"Retry-After": "1"}),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", lambda s: None)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)

    with pytest.raises(requests.HTTPError):
        client.download_url("https://example.invalid/file.xml")


@pytest.mark.unit
def test_download_url_retries_on_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(
        [
            FakeResponse(status_code=503, content=b""),
            FakeResponse(status_code=200, content=b"recovered"),
        ]
    )
    client = NZLegislationClient(
        make_settings(min_seconds_between_requests=0.0, max_retries=2), session=session
    )
    sleeps: list[float] = []
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.sleep", sleeps.append)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("nz_legislation_corpus.nz_api.random.random", lambda: 0.0)

    content = client.download_url("https://example.invalid/file.xml")

    assert content == b"recovered"
    assert len(sleeps) == 1
