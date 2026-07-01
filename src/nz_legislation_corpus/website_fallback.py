from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from .utils import sha256_bytes, sha256_text, utc_now_iso

OFFICIAL_LEGISLATION_HOSTS = ("legislation.govt.nz", "www.legislation.govt.nz")
FALLBACK_SCHEMA_VERSION = "1.0"
DEFAULT_RETRY_LIMIT = 25


@dataclass(frozen=True)
class OfficialWebsiteFallbackPolicy:
    """Policy for conservative fallback retrieval from the official website."""

    allowed_hosts: tuple[str, ...] = OFFICIAL_LEGISLATION_HOSTS
    allow_browser_rendering: bool = False
    max_records: int = DEFAULT_RETRY_LIMIT
    require_https: bool = True


@dataclass(frozen=True)
class FailedRecord:
    """Minimal retry input for a record that already failed API/XML/HTML attempts."""

    record_id: str
    source_url: str | None = None
    previous_failure_reason: str = ""
    html_url: str | None = None
    canonical_url: str | None = None
    source_title: str | None = None


@dataclass(frozen=True)
class FallbackAttempt:
    """A single ordered fallback attempt plus the provenance fields we retain."""

    source_url: str
    retrieval_method: str
    previous_failure_reason: str
    retrieval_timestamp_utc: str
    confidence: str
    status: str
    content_hash: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "retrieval_method": self.retrieval_method,
            "retrieval_timestamp_utc": self.retrieval_timestamp_utc,
            "content_hash": self.content_hash,
            "previous_failure_reason": self.previous_failure_reason,
            "confidence": self.confidence,
            "status": self.status,
        }


@dataclass(frozen=True)
class FallbackPlan:
    """A conservative retry plan for one failed record."""

    record_id: str
    source_url: str | None
    previous_failure_reason: str
    status: str
    warning: str
    eligible: bool
    attempts: tuple[FallbackAttempt, ...] = field(default_factory=tuple)
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_url": self.source_url,
            "previous_failure_reason": self.previous_failure_reason,
            "status": self.status,
            "warning": self.warning,
            "eligible": self.eligible,
            "attempts": [attempt.as_dict() for attempt in self.attempts],
            "provenance": self.provenance,
        }


def _record_value(record: Mapping[str, Any] | FailedRecord, key: str) -> Any:
    if isinstance(record, FailedRecord):
        return getattr(record, key)
    return record.get(key)


def _normalize_host(hostname: str) -> str:
    return hostname.lower().removeprefix("www.")


def is_public_official_url(
    url: str | None,
    *,
    policy: OfficialWebsiteFallbackPolicy | None = None,
) -> bool:
    """Return True only for public HTTPS URLs on the official legislation host."""
    if not url:
        return False
    parsed = urlparse(url)
    effective_policy = policy or OfficialWebsiteFallbackPolicy()
    if effective_policy.require_https and parsed.scheme.lower() != "https":
        return False
    if parsed.username or parsed.password:
        return False
    host = _normalize_host(parsed.hostname or "")
    if not host:
        return False
    allowed_hosts = {_normalize_host(candidate) for candidate in effective_policy.allowed_hosts}
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts)


def alternate_dated_url(url: str | None) -> str | None:
    """Return a conservative alternate dated URL when the path ends in YYYY-MM-DD."""
    if not url:
        return None
    import re

    match = re.search(r"(?P<date>\d{4}-\d{2}-\d{2})(?P<suffix>\.html|\.htm|/)?$", url)
    if not match:
        return None
    suffix = match.group("suffix") or ""
    return f"{url[: match.start('date')]}{match.group('date')}A{suffix}"


def build_fallback_attempt_provenance(
    *,
    source_url: str,
    retrieval_method: str,
    previous_failure_reason: str,
    confidence: str,
    status: str,
    content: bytes | str | None = None,
    content_hash: str | None = None,
    retrieval_timestamp_utc: str | None = None,
) -> dict[str, Any]:
    """Build the provenance payload for one fallback attempt."""
    if content_hash is None and content is not None:
        content_hash = sha256_bytes(content) if isinstance(content, bytes) else sha256_text(content)
    return FallbackAttempt(
        source_url=source_url,
        retrieval_method=retrieval_method,
        previous_failure_reason=previous_failure_reason,
        retrieval_timestamp_utc=retrieval_timestamp_utc or utc_now_iso(),
        confidence=confidence,
        status=status,
        content_hash=content_hash,
    ).as_dict()


def _fallback_attempts_for_record(
    record: Mapping[str, Any] | FailedRecord,
    *,
    policy: OfficialWebsiteFallbackPolicy,
    retrieval_timestamp_utc: str,
) -> tuple[FallbackAttempt, ...]:
    source_url = _record_value(record, "source_url") or _record_value(record, "html_url")
    previous_failure_reason = str(_record_value(record, "previous_failure_reason") or "")
    html_url = _record_value(record, "html_url") or source_url
    canonical_url = _record_value(record, "canonical_url") or source_url

    attempts: list[FallbackAttempt] = []

    if is_public_official_url(html_url, policy=policy):
        attempts.append(
            FallbackAttempt(
                source_url=str(html_url),
                retrieval_method="official_website_html",
                previous_failure_reason=previous_failure_reason,
                retrieval_timestamp_utc=retrieval_timestamp_utc,
                confidence="medium",
                status="planned",
            )
        )

    dated_url = alternate_dated_url(str(html_url) if html_url else None)
    if dated_url and dated_url != html_url and is_public_official_url(dated_url, policy=policy):
        attempts.append(
            FallbackAttempt(
                source_url=dated_url,
                retrieval_method="official_website_alternate_dated_url",
                previous_failure_reason=previous_failure_reason,
                retrieval_timestamp_utc=retrieval_timestamp_utc,
                confidence="medium",
                status="planned",
            )
        )

    if policy.allow_browser_rendering and is_public_official_url(canonical_url, policy=policy):
        attempts.append(
            FallbackAttempt(
                source_url=str(canonical_url),
                retrieval_method="official_website_rendered_html",
                previous_failure_reason=previous_failure_reason,
                retrieval_timestamp_utc=retrieval_timestamp_utc,
                confidence="low",
                status="planned",
            )
        )

    return tuple(attempts)


def build_failed_record_retry_plan(
    record: Mapping[str, Any] | FailedRecord,
    *,
    policy: OfficialWebsiteFallbackPolicy | None = None,
    retrieval_timestamp_utc: str | None = None,
) -> dict[str, Any]:
    """Return a fail-closed retry plan for one failed record."""
    effective_policy = policy or OfficialWebsiteFallbackPolicy()
    timestamp = retrieval_timestamp_utc or utc_now_iso()
    record_id = str(_record_value(record, "record_id") or _record_value(record, "stable_id") or "")
    source_url = _record_value(record, "source_url") or _record_value(record, "html_url")
    previous_failure_reason = str(_record_value(record, "previous_failure_reason") or "")

    public_source_eligible = is_public_official_url(source_url, policy=effective_policy)
    attempts = _fallback_attempts_for_record(
        record,
        policy=effective_policy,
        retrieval_timestamp_utc=timestamp,
    )

    eligible = bool(attempts) and public_source_eligible
    if not eligible:
        warning = (
            f"Official website fallback blocked for {record_id or '<unknown>'}: "
            "no eligible public official URL was available; fail closed."
        )
        return FallbackPlan(
            record_id=record_id,
            source_url=str(source_url) if source_url else None,
            previous_failure_reason=previous_failure_reason,
            status="blocked",
            warning=warning,
            eligible=False,
            attempts=(),
            provenance={
                "schema_version": FALLBACK_SCHEMA_VERSION,
                "retrieval_method": "official_website_fallback",
                "retrieval_timestamp_utc": timestamp,
                "source_url": str(source_url) if source_url else None,
                "content_hash": None,
                "previous_failure_reason": previous_failure_reason,
                "confidence": "blocked",
                "status": "blocked",
            },
        ).as_dict()

    warning = (
        f"Official website fallback queued for {record_id or '<unknown>'} "
        f"after {previous_failure_reason or 'prior retrieval failures'}."
    )
    provenance = {
        "schema_version": FALLBACK_SCHEMA_VERSION,
        "retrieval_method": "official_website_fallback",
        "retrieval_timestamp_utc": timestamp,
        "source_url": str(source_url) if source_url else attempts[0].source_url,
        "content_hash": None,
        "previous_failure_reason": previous_failure_reason,
        "confidence": "medium" if attempts else "blocked",
        "status": "queued",
    }
    return FallbackPlan(
        record_id=record_id,
        source_url=str(source_url) if source_url else None,
        previous_failure_reason=previous_failure_reason,
        status="queued",
        warning=warning,
        eligible=True,
        attempts=attempts,
        provenance=provenance,
    ).as_dict()


def plan_failed_record_retries(
    failed_records: Sequence[Mapping[str, Any] | FailedRecord],
    *,
    policy: OfficialWebsiteFallbackPolicy | None = None,
    max_records: int | None = None,
    retrieval_timestamp_utc: str | None = None,
) -> dict[str, Any]:
    """Build a conservative retry plan for a small failed-record set."""
    effective_policy = policy or OfficialWebsiteFallbackPolicy()
    timestamp = retrieval_timestamp_utc or utc_now_iso()
    limit = max_records if max_records is not None else effective_policy.max_records
    selected_records = failed_records[:limit]

    plans = [
        build_failed_record_retry_plan(
            record,
            policy=effective_policy,
            retrieval_timestamp_utc=timestamp,
        )
        for record in selected_records
    ]
    warnings = [str(plan["warning"]) for plan in plans if plan.get("warning")]
    if len(failed_records) > len(selected_records):
        warnings.append(
            f"Skipped {len(failed_records) - len(selected_records)} failed record(s) "
            f"because the retry planner is limited to {len(selected_records)} record(s)."
        )
    return {
        "schema_version": FALLBACK_SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "policy": {
            "allowed_hosts": list(effective_policy.allowed_hosts),
            "allow_browser_rendering": effective_policy.allow_browser_rendering,
            "max_records": effective_policy.max_records,
            "require_https": effective_policy.require_https,
        },
        "record_count": len(failed_records),
        "planned_count": len(plans),
        "blocked_count": sum(1 for plan in plans if plan.get("status") == "blocked"),
        "warnings": warnings,
        "records": plans,
    }
