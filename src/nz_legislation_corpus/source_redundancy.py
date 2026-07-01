from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .utils import sha256_text

SourceStatus = Literal[
    "canonical_api",
    "official_html_fallback",
    "alternate_dated_url",
    "official_website_fallback",
    "secondary_corroborated",
    "rescued_secondary",
    "unresolved",
]

AttemptStatus = Literal["success", "failed", "blocked", "skipped"]
Confidence = Literal["high", "medium", "low", "unknown"]

SOURCE_PRIORITY: tuple[SourceStatus, ...] = (
    "canonical_api",
    "official_html_fallback",
    "alternate_dated_url",
    "official_website_fallback",
    "secondary_corroborated",
    "rescued_secondary",
    "unresolved",
)

CANONICAL_STATUSES: frozenset[SourceStatus] = frozenset(
    {
        "canonical_api",
        "official_html_fallback",
        "alternate_dated_url",
    }
)

MANUAL_REVIEW_STATUSES: frozenset[SourceStatus] = frozenset(
    {
        "official_website_fallback",
        "secondary_corroborated",
        "rescued_secondary",
        "unresolved",
    }
)

STATUS_BY_METHOD: dict[str, SourceStatus] = {
    "api_xml": "canonical_api",
    "official_html": "official_html_fallback",
    "alternate_dated_url": "alternate_dated_url",
    "official_website": "official_website_fallback",
    "nzlii_candidate": "secondary_corroborated",
    "nzlii_rescue": "rescued_secondary",
}


@dataclass(frozen=True, slots=True)
class RetrievalAttempt:
    """Auditable retrieval attempt for a source or fallback candidate."""

    source_name: str
    url: str
    method: str
    retrieved_at: str | None
    status: AttemptStatus
    content_sha256: str | None = None
    warning: str | None = None
    error: str | None = None
    canonical: bool = False
    confidence: Confidence = "unknown"
    rights_note: str | None = None

    @classmethod
    def from_content(
        cls,
        *,
        source_name: str,
        url: str,
        method: str,
        retrieved_at: str | None,
        content: str | bytes,
        canonical: bool = False,
        confidence: Confidence = "high",
        warning: str | None = None,
        rights_note: str | None = None,
    ) -> RetrievalAttempt:
        """Build a successful attempt with a deterministic content hash."""
        if isinstance(content, bytes):
            content_hash = sha256_text(content.decode("utf-8", errors="replace"))
        else:
            content_hash = sha256_text(content)
        return cls(
            source_name=source_name,
            url=url,
            method=method,
            retrieved_at=retrieved_at,
            status="success",
            content_sha256=content_hash,
            canonical=canonical,
            confidence=confidence,
            warning=warning,
            rights_note=rights_note,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable attempt."""
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True, slots=True)
class SourceDecision:
    """Final resolver decision for one record."""

    status: SourceStatus
    selected_source: str | None
    selected_url: str | None
    selected_method: str | None
    confidence: Confidence
    canonical: bool
    manual_review_required: bool
    attempts: tuple[RetrievalAttempt, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable decision."""
        return {
            "status": self.status,
            "selected_source": self.selected_source,
            "selected_url": self.selected_url,
            "selected_method": self.selected_method,
            "confidence": self.confidence,
            "canonical": self.canonical,
            "manual_review_required": self.manual_review_required,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


def status_for_attempt(attempt: RetrievalAttempt) -> SourceStatus:
    """Classify a successful retrieval attempt by its method/source."""
    if attempt.status != "success":
        return "unresolved"
    if attempt.canonical:
        return "canonical_api"
    return STATUS_BY_METHOD.get(attempt.method, "unresolved")


def decide_source(
    attempts: list[RetrievalAttempt] | tuple[RetrievalAttempt, ...],
) -> SourceDecision:
    """Choose the highest-priority successful source attempt."""
    ordered_attempts = tuple(attempts)
    successful: list[tuple[int, SourceStatus, RetrievalAttempt]] = []
    for attempt in ordered_attempts:
        status = status_for_attempt(attempt)
        if attempt.status == "success":
            successful.append((SOURCE_PRIORITY.index(status), status, attempt))

    if not successful:
        return SourceDecision(
            status="unresolved",
            selected_source=None,
            selected_url=None,
            selected_method=None,
            confidence="unknown",
            canonical=False,
            manual_review_required=True,
            attempts=ordered_attempts,
        )

    _, status, selected = sorted(successful, key=lambda item: item[0])[0]
    canonical = status in CANONICAL_STATUSES
    return SourceDecision(
        status=status,
        selected_source=selected.source_name,
        selected_url=selected.url,
        selected_method=selected.method,
        confidence=selected.confidence,
        canonical=canonical,
        manual_review_required=status in MANUAL_REVIEW_STATUSES or not canonical,
        attempts=ordered_attempts,
    )


def decision_from_record(record: dict[str, Any]) -> SourceDecision | None:
    """Read source redundancy metadata from a normalized record when present."""
    raw = record.get("source_redundancy")
    if not isinstance(raw, dict):
        return None
    attempts = []
    for item in raw.get("attempts") or []:
        if not isinstance(item, dict):
            continue
        attempts.append(
            RetrievalAttempt(
                source_name=str(item.get("source_name") or ""),
                url=str(item.get("url") or ""),
                method=str(item.get("method") or ""),
                retrieved_at=item.get("retrieved_at"),
                status=item.get("status")
                if item.get("status") in {"success", "failed", "blocked", "skipped"}
                else "failed",
                content_sha256=item.get("content_sha256"),
                warning=item.get("warning"),
                error=item.get("error"),
                canonical=bool(item.get("canonical")),
                confidence=item.get("confidence")
                if item.get("confidence") in {"high", "medium", "low", "unknown"}
                else "unknown",
                rights_note=item.get("rights_note"),
            )
        )
    if attempts:
        return decide_source(attempts)
    status = raw.get("status")
    if status not in SOURCE_PRIORITY:
        return None
    return SourceDecision(
        status=status,
        selected_source=raw.get("selected_source"),
        selected_url=raw.get("selected_url"),
        selected_method=raw.get("selected_method"),
        confidence=raw.get("confidence")
        if raw.get("confidence") in {"high", "medium", "low", "unknown"}
        else "unknown",
        canonical=status in CANONICAL_STATUSES,
        manual_review_required=status in MANUAL_REVIEW_STATUSES,
    )


def summarize_source_redundancy(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize fallback/secondary source use across records."""
    counts = dict.fromkeys(SOURCE_PRIORITY, 0)
    manual_review_ids: list[str] = []
    records_with_metadata = 0

    for record in records:
        decision = decision_from_record(record)
        if decision is None:
            continue
        records_with_metadata += 1
        counts[decision.status] += 1
        if decision.manual_review_required:
            manual_review_ids.append(str(record.get("stable_id") or record.get("version_id") or ""))

    return {
        "schema_version": "1.0",
        "records_with_source_redundancy": records_with_metadata,
        "status_counts": counts,
        "manual_review_required_count": len(manual_review_ids),
        "manual_review_stable_ids": [value for value in manual_review_ids if value],
    }
