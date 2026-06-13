from __future__ import annotations

import logging
import random
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.parse import urljoin

import requests

from .config import Settings, require

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NZAPIResponse:
    data: dict[str, Any] | list[Any]
    headers: dict[str, str]


class HTTPResponse(Protocol):
    status_code: int
    headers: Mapping[str, str]
    content: bytes
    text: str

    def json(self) -> Any: ...
    def raise_for_status(self) -> None: ...


class HTTPSession(Protocol):
    def request(self, method: str, url: str, **kwargs: Any) -> HTTPResponse: ...
    def get(self, url: str, **kwargs: Any) -> HTTPResponse: ...


class NZLegislationClient:
    """Client for the official New Zealand Legislation API.

    The client is intentionally conservative: it uses X-Api-Key auth, obeys 429 Retry-After
    where present, slows down on low remaining quotas, and treats HTTP 403 as a possible burst
    limit event.
    """

    def __init__(self, settings: Settings, session: HTTPSession | None = None):
        self.settings = settings
        self.api_key = require(settings.nz_api_key, "NZ_LEGISLATION_API_KEY")
        self.base_url = settings.nz_api_base_url.rstrip("/") + "/"
        self.session: HTTPSession = (
            session if session is not None else cast("HTTPSession", requests.Session())
        )
        self.last_request_at = 0.0

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _sleep_for_pacing(self) -> None:
        elapsed = time.monotonic() - self.last_request_at
        wait = self.settings.min_seconds_between_requests - elapsed
        if wait > 0:
            time.sleep(wait)

    @staticmethod
    def _parse_int_header(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(str(value).strip())
        except ValueError:
            return None

    def _sleep_for_low_quota(self, headers: Mapping[str, str]) -> None:
        remaining = self._parse_int_header(headers.get("X-RateLimit-Remaining"))
        reset = self._parse_int_header(headers.get("X-RateLimit-Reset"))
        if remaining is None or reset is None:
            return
        if remaining > self.settings.rate_limit_low_watermark:
            return
        wait_until_reset = max(0.0, reset - time.time())
        if wait_until_reset <= 0:
            return
        sleep_seconds_raw = max(
            self.settings.rate_limit_reset_padding_seconds,
            wait_until_reset / max(1, remaining),
        )
        sleep_seconds = min(sleep_seconds_raw, self.settings.rate_limit_max_sleep_seconds)
        if sleep_seconds_raw > self.settings.rate_limit_max_sleep_seconds:
            log.warning(
                "NZ API quota low; sleep capped at %.1fs (raw=%.1fs, remaining=%s reset=%s)",
                sleep_seconds,
                sleep_seconds_raw,
                remaining,
                reset,
            )
        else:
            log.warning(
                "NZ API quota low (remaining=%s reset=%s); sleeping %.1fs",
                remaining,
                reset,
                sleep_seconds,
            )
        time.sleep(sleep_seconds)

    @staticmethod
    def _retry_after_seconds(response: HTTPResponse, *, fallback_attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        return min(120, (2**fallback_attempt) + random.random())

    def request_json(self, method: str, path: str, **kwargs: Any) -> NZAPIResponse:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["X-Api-Key"] = self.api_key
        headers.setdefault("Accept", "application/json")
        timeout = kwargs.pop("timeout", self.settings.request_timeout_seconds)
        url = self._url(path)

        for attempt in range(1, self.settings.max_retries + 1):
            self._sleep_for_pacing()
            self.last_request_at = time.monotonic()
            response = self.session.request(method, url, headers=headers, timeout=timeout, **kwargs)
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            if remaining is not None:
                log.debug("NZ API remaining quota: %s reset=%s", remaining, reset)

            if response.status_code == 429:
                sleep_seconds = self._retry_after_seconds(response, fallback_attempt=attempt)
                log.warning("NZ API 429 rate limited; sleeping %.1fs", sleep_seconds)
                time.sleep(sleep_seconds)
                continue

            if response.status_code == 403 and attempt < self.settings.max_retries:
                # The docs describe an IP burst limit that returns 403. Be conservative.
                sleep_seconds = min(300, 30 * attempt + random.random())
                log.warning(
                    "NZ API returned 403; treating as possible burst limit and sleeping %.1fs",
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)
                continue

            if response.status_code >= 500 and attempt < self.settings.max_retries:
                sleep_seconds = min(60, (2**attempt) + random.random())
                log.warning("NZ API %s; retrying after %.1fs", response.status_code, sleep_seconds)
                time.sleep(sleep_seconds)
                continue

            response.raise_for_status()
            self._sleep_for_low_quota(response.headers)
            return NZAPIResponse(data=response.json(), headers=dict(response.headers))

        raise RuntimeError(
            f"NZ API request failed after {self.settings.max_retries} attempts: {method} {url}"
        )

    def download_url(self, url: str, *, accept: str | None = None) -> bytes:
        headers = {"X-Api-Key": self.api_key}
        if accept:
            headers["Accept"] = accept
        for attempt in range(1, self.settings.max_retries + 1):
            self._sleep_for_pacing()
            self.last_request_at = time.monotonic()
            response = self.session.get(
                url, headers=headers, timeout=self.settings.request_timeout_seconds
            )
            if response.status_code == 429 and attempt < self.settings.max_retries:
                sleep_seconds = self._retry_after_seconds(response, fallback_attempt=attempt)
                log.warning(
                    "Download throttled (%s); sleeping %.1fs", response.status_code, sleep_seconds
                )
                time.sleep(sleep_seconds)
                continue
            if response.status_code == 403 and attempt < self.settings.max_retries:
                sleep_seconds = min(300, 30 * attempt + random.random())
                log.warning(
                    "Download throttled (%s); sleeping %.1fs", response.status_code, sleep_seconds
                )
                time.sleep(sleep_seconds)
                continue
            if response.status_code >= 500 and attempt < self.settings.max_retries:
                time.sleep(min(60, (2**attempt) + random.random()))
                continue
            response.raise_for_status()
            self._sleep_for_low_quota(response.headers)
            return response.content
        raise RuntimeError(f"Download failed after retries: {url}")

    def search_works(
        self,
        *,
        search_term: str,
        search_field: str = "title",
        page: int = 1,
        per_page: int | None = None,
        legislation_type: str | None = None,
        legislation_status: str | None = None,
        sort_by: str | None = None,
        publisher: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "search_term": search_term,
            "search_field": search_field,
            "page": page,
            "per_page": per_page or self.settings.per_page,
        }
        if legislation_type:
            params["legislation_type"] = legislation_type
        if legislation_status:
            params["legislation_status"] = legislation_status
        if sort_by:
            params["sort_by"] = sort_by
        if publisher:
            params["publisher"] = publisher
        return cast("dict[str, Any]", self.request_json("GET", "works/", params=params).data)

    def iter_search_works(
        self,
        *,
        search_term: str,
        search_field: str = "title",
        per_page: int | None = None,
        max_pages: int | None = None,
        legislation_type: str | None = None,
        legislation_status: str | None = None,
        sort_by: str | None = None,
        publisher: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        page = 1
        seen: set[str] = set()
        while True:
            payload = self.search_works(
                search_term=search_term,
                search_field=search_field,
                page=page,
                per_page=per_page,
                legislation_type=legislation_type,
                legislation_status=legislation_status,
                sort_by=sort_by,
                publisher=publisher,
            )
            results = payload.get("results", []) if isinstance(payload, dict) else []
            for work in results:
                work_id = str(work.get("work_id", ""))
                if work_id and work_id not in seen:
                    seen.add(work_id)
                    yield work
            total = int(payload.get("total", 0) or 0) if isinstance(payload, dict) else 0
            returned = page * int(
                payload.get("per_page", per_page or self.settings.per_page)
                or self.settings.per_page
            )
            if not results or (total and returned >= total):
                break
            page += 1
            if max_pages and page > max_pages:
                break

    def get_work_versions(self, work_id: str, *, sort: str = "desc") -> dict[str, Any]:
        return cast(
            "dict[str, Any]",
            self.request_json("GET", f"works/{work_id}/versions/", params={"sort": sort}).data,
        )

    def iter_work_versions(self, work_id: str, *, sort: str = "desc") -> Iterator[dict[str, Any]]:
        payload = self.get_work_versions(work_id, sort=sort)
        results = payload.get("results", []) if isinstance(payload, dict) else []
        yield from results

    def get_version(self, version_id: str) -> dict[str, Any]:
        return cast("dict[str, Any]", self.request_json("GET", f"versions/{version_id}/").data)

    @staticmethod
    def format_url(version: dict[str, Any], fmt: str) -> str | None:
        for item in version.get("formats", []) or []:
            if str(item.get("type", "")).lower() == fmt.lower():
                return item.get("url")
        return None

    def discover_versions(
        self,
        *,
        search_terms: list[str],
        search_field: str,
        seed_work_ids: list[str] | None = None,
        latest_only: bool = False,
        max_works: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield version metadata from search terms and/or seed work IDs.

        The official API is search-oriented, not an obvious "enumerate every work changed since X"
        feed. This function is therefore configurable: seed files are safest for deterministic
        bootstraps; search terms are a convenience for discovery.
        """
        seen_works: set[str] = set()
        seen_versions: set[str] = set()

        if seed_work_ids:
            for work_id in seed_work_ids:
                if work_id and work_id not in seen_works:
                    if max_works is not None and len(seen_works) >= max_works:
                        return
                    seen_works.add(work_id)
                    for version in self.iter_work_versions(work_id):
                        version_id = str(version.get("version_id", ""))
                        if version_id and version_id not in seen_versions:
                            seen_versions.add(version_id)
                            yield version if not latest_only else self.get_version(version_id)
                            if latest_only:
                                break

        type_filters = self.settings.legislation_types or [None]
        for term in search_terms:
            for leg_type in type_filters:
                work_iter = self.iter_search_works(
                    search_term=term,
                    search_field=search_field,
                    legislation_type=leg_type,
                    legislation_status=self.settings.legislation_status,
                    sort_by=self.settings.search_sort_by,
                    publisher=self.settings.publisher,
                )
                for work in work_iter:
                    work_id = str(work.get("work_id", ""))
                    if not work_id or work_id in seen_works:
                        continue
                    if max_works is not None and len(seen_works) >= max_works:
                        return
                    seen_works.add(work_id)
                    if latest_only and isinstance(work.get("latest_matching_version"), dict):
                        version = work["latest_matching_version"]
                        version_id = str(version.get("version_id", ""))
                        if version_id and version_id not in seen_versions:
                            seen_versions.add(version_id)
                            yield self.get_version(version_id)
                        continue
                    for version in self.iter_work_versions(work_id):
                        version_id = str(version.get("version_id", ""))
                        if version_id and version_id not in seen_versions:
                            seen_versions.add(version_id)
                            yield version
