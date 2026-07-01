from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

from .utils import write_json

NZLII_SOURCE_INVENTORY = [
    {
        "collection": "New Zealand Acts",
        "url_pattern": "https://www.nzlii.org/nz/legis/hist_act/",
        "role": "secondary_coverage_check",
        "access_policy": "conservative_manual_or_supplied_metadata_only",
        "canonical_status": "not_canonical",
        "caveat": "Historical coverage, formatting, and update cadence may differ from NZ Legislation.",
    },
    {
        "collection": "New Zealand Regulations",
        "url_pattern": "https://www.nzlii.org/nz/legis/num_reg/",
        "role": "secondary_coverage_check",
        "access_policy": "conservative_manual_or_supplied_metadata_only",
        "canonical_status": "not_canonical",
        "caveat": "Candidate matches require manual review before any text rescue.",
    },
]

NZLIIMatchClassification = Literal[
    "exact",
    "probable",
    "ambiguous",
    "missing",
    "out_of_scope",
]

_TOKEN_RE = re.compile(r"[^a-z0-9]+")
_NOISE_WORDS = {
    "act",
    "bill",
    "amendment",
    "order",
    "regulation",
    "regulations",
    "new",
    "zealand",
}


@dataclass(frozen=True)
class OfficialMetadataRecord:
    work_id: str
    version_id: str | None = None
    title: str = ""
    date: str | None = None
    source_url: str | None = None
    content_hash: str | None = None
    in_scope: bool = True


@dataclass(frozen=True)
class NZLIICandidateRecord:
    url: str
    title: str
    date: str | None
    retrieved_at: str | None
    content_hash: str
    confidence: float
    classification: NZLIIMatchClassification


@dataclass(frozen=True)
class NZLIIReviewCandidate:
    official_work_id: str
    official_version_id: str | None
    official_title: str
    official_date: str | None
    classification: NZLIIMatchClassification
    confidence: float
    selected_candidate: NZLIICandidateRecord | None
    candidate_count: int
    candidate_matches: list[NZLIICandidateRecord] = field(default_factory=list)
    review_required: bool = False
    reason: str = ""


def _coerce_record(value: OfficialMetadataRecord | Mapping[str, Any]) -> OfficialMetadataRecord:
    if isinstance(value, OfficialMetadataRecord):
        return value
    return OfficialMetadataRecord(
        work_id=str(value.get("work_id") or value.get("record_id") or "").strip(),
        version_id=(
            str(value.get("version_id")).strip()
            if value.get("version_id") not in {None, ""}
            else None
        ),
        title=str(value.get("title") or value.get("display_title") or "").strip(),
        date=_normalize_date(
            value.get("date") or value.get("published_date") or value.get("effective_date")
        ),
        source_url=(
            str(value.get("source_url")).strip()
            if value.get("source_url") not in {None, ""}
            else None
        ),
        content_hash=(
            str(value.get("content_hash")).strip()
            if value.get("content_hash") not in {None, ""}
            else None
        ),
        in_scope=bool(value.get("in_scope", True)),
    )


def _coerce_candidate(value: NZLIICandidateRecord | Mapping[str, Any]) -> NZLIICandidateRecord:
    if isinstance(value, NZLIICandidateRecord):
        return value
    classification = value.get("classification")
    if classification not in {"exact", "probable", "ambiguous", "missing", "out_of_scope"}:
        classification = "missing"
    return NZLIICandidateRecord(
        url=str(value.get("url") or "").strip(),
        title=str(value.get("title") or "").strip(),
        date=_normalize_date(value.get("date")),
        retrieved_at=(
            str(value.get("retrieved_at")).strip()
            if value.get("retrieved_at") not in {None, ""}
            else None
        ),
        content_hash=str(value.get("content_hash") or "").strip(),
        confidence=float(value.get("confidence") or 0.0),
        classification=classification,
    )


def _normalize_date(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return text


def _normalize_text(value: str) -> str:
    return " ".join(_TOKEN_RE.sub(" ", value.lower()).split())


def _token_set(value: str) -> set[str]:
    return {
        token for token in _normalize_text(value).split() if token and token not in _NOISE_WORDS
    }


def _date_distance_days(left: str | None, right: str | None) -> int | None:
    if not left or not right:
        return None
    try:
        delta = date.fromisoformat(left) - date.fromisoformat(right)
    except ValueError:
        return None
    return abs(delta.days)


def _title_similarity(official_title: str, candidate_title: str) -> float:
    left = _token_set(official_title)
    right = _token_set(candidate_title)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    overlap = len(left & right)
    union = len(left | right)
    return overlap / union if union else 0.0


def _score_candidate(
    official: OfficialMetadataRecord,
    candidate: NZLIICandidateRecord,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    if official.content_hash and official.content_hash == candidate.content_hash:
        return 1.0, ["content_hash_match"]

    official_title = _normalize_text(official.title)
    candidate_title = _normalize_text(candidate.title)
    if official_title and official_title == candidate_title:
        score += 0.6
        reasons.append("title_match")
    else:
        similarity = _title_similarity(official.title, candidate.title)
        if similarity >= 0.7:
            score += 0.35
            reasons.append("title_close")
        elif similarity >= 0.45:
            score += 0.2
            reasons.append("title_related")

    date_distance = _date_distance_days(official.date, candidate.date)
    if official.date and candidate.date:
        if date_distance == 0:
            score += 0.3
            reasons.append("date_match")
        elif date_distance is not None and date_distance <= 7:
            score += 0.15
            reasons.append("date_near")

    if official.source_url and official.source_url.rstrip("/") == candidate.url.rstrip("/"):
        score += 0.1
        reasons.append("url_match")

    if official.content_hash and candidate.content_hash:
        hash_prefix = official.content_hash[:12]
        if candidate.content_hash.startswith(hash_prefix):
            score += 0.05
            reasons.append("hash_prefix_related")

    return min(score, 1.0), reasons


def classify_official_record(
    official_record: OfficialMetadataRecord | Mapping[str, Any],
    candidates: Sequence[NZLIICandidateRecord | Mapping[str, Any]],
) -> NZLIIReviewCandidate:
    official = _coerce_record(official_record)
    candidate_records = [_coerce_candidate(candidate) for candidate in candidates]
    classification: NZLIIMatchClassification = "missing"
    confidence = 0.0
    selected_candidate: NZLIICandidateRecord | None = None
    candidate_matches: list[NZLIICandidateRecord] = []
    review_required = False
    reason = "no_candidate_crossed_match_threshold"

    if not official.in_scope:
        classification = "out_of_scope"
        confidence = 0.0
        reason = "official_record_marked_out_of_scope"
    elif candidate_records:
        scored = [
            (candidate, *_score_candidate(official, candidate)) for candidate in candidate_records
        ]
        scored.sort(key=lambda item: (-item[1], item[0].url, item[0].title))

        best_candidate, best_score, _best_reasons = scored[0]
        second_score = scored[1][1] if len(scored) > 1 else None

        exact_matches = [
            candidate
            for candidate, _score, _reasons in scored
            if _normalize_text(candidate.title) == _normalize_text(official.title)
            and candidate.date == official.date
        ]
        exact_content_hash_matches = [
            candidate
            for candidate, _score, _reasons in scored
            if official.content_hash and candidate.content_hash == official.content_hash
        ]
        probable_matches = [candidate for candidate, score, _reasons in scored if score >= 0.6]

        if exact_content_hash_matches and len(exact_content_hash_matches) == 1:
            classification = "exact"
            confidence = 1.0
            selected_candidate = exact_content_hash_matches[0]
            candidate_matches = [selected_candidate]
            reason = "exact_title_date_or_hash_match"
        elif len(exact_matches) == 1 and best_score >= 0.85:
            classification = "exact"
            confidence = 1.0
            selected_candidate = exact_matches[0]
            candidate_matches = [selected_candidate]
            reason = "exact_title_date_or_hash_match"
        elif len(exact_matches) > 1 or len(exact_content_hash_matches) > 1:
            exact_candidates = exact_content_hash_matches or exact_matches
            classification = "ambiguous"
            confidence = 1.0
            selected_candidate = exact_candidates[0]
            candidate_matches = exact_candidates[:3]
            review_required = True
            reason = "multiple_exact_matches"
        elif (
            len(probable_matches) > 1
            and second_score is not None
            and best_score - second_score <= 0.05
        ):
            classification = "ambiguous"
            confidence = round(best_score, 3)
            selected_candidate = best_candidate
            candidate_matches = probable_matches[:3]
            review_required = True
            reason = "multiple_candidates_with_similar_score"
        elif best_score >= 0.6:
            classification = "probable"
            confidence = round(best_score, 3)
            selected_candidate = best_candidate
            candidate_matches = [best_candidate]
            review_required = True
            reason = "single_best_candidate_requires_manual_review"
        else:
            classification = "missing"
            confidence = round(best_score, 3)
            reason = "no_candidate_crossed_match_threshold"

    return NZLIIReviewCandidate(
        official_work_id=official.work_id,
        official_version_id=official.version_id,
        official_title=official.title,
        official_date=official.date,
        classification=classification,
        confidence=confidence,
        selected_candidate=selected_candidate,
        candidate_count=len(candidate_records),
        candidate_matches=candidate_matches,
        review_required=review_required,
        reason=reason,
    )


def build_nzlii_reconciliation_report(
    official_records: Sequence[OfficialMetadataRecord | Mapping[str, Any]],
    candidate_groups: Mapping[str, Sequence[NZLIICandidateRecord | Mapping[str, Any]]],
    *,
    seed_work_ids: Sequence[str] | None = None,
    bootstrap_failure_ids: Sequence[str] | None = None,
    bootstrap_failure_records: Sequence[Mapping[str, Any]] | None = None,
    review_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report_rows: list[dict[str, Any]] = []
    manual_review_candidates: list[dict[str, Any]] = []
    classification_counts: dict[str, int] = {
        "exact": 0,
        "probable": 0,
        "ambiguous": 0,
        "missing": 0,
        "out_of_scope": 0,
    }

    for official_item in official_records:
        official = _coerce_record(official_item)
        if official.version_id is not None and official.version_id in candidate_groups:
            candidates = candidate_groups.get(official.version_id, ())
        else:
            candidates = candidate_groups.get(official.work_id, ())
        result = classify_official_record(official, candidates)
        classification_counts[result.classification] += 1

        row = {
            "official_work_id": result.official_work_id,
            "official_version_id": result.official_version_id,
            "official_title": result.official_title,
            "official_date": result.official_date,
            "classification": result.classification,
            "confidence": result.confidence,
            "candidate_count": result.candidate_count,
            "selected_candidate": _candidate_to_dict(
                result.selected_candidate, classification=result.classification
            ),
            "candidate_matches": [
                _candidate_to_dict(candidate, classification=result.classification)
                for candidate in result.candidate_matches
            ],
            "review_required": result.review_required,
            "reason": result.reason,
        }
        report_rows.append(row)
        if result.review_required:
            manual_review_candidates.append(row)

    report_rows.sort(key=lambda item: (item["official_work_id"], item["official_version_id"] or ""))
    manual_review_candidates.sort(
        key=lambda item: (item["official_work_id"], item["official_version_id"] or "")
    )

    seed_ids = sorted({work_id.strip() for work_id in seed_work_ids or [] if work_id.strip()})
    failure_records_by_id = _failure_records_by_id(bootstrap_failure_records or [])
    failed_ids = sorted(
        {
            work_id.strip()
            for work_id in [
                *(bootstrap_failure_ids or []),
                *failure_records_by_id,
            ]
            if work_id.strip()
        }
    )
    exact_or_probable = {
        str(row["official_work_id"])
        for row in report_rows
        if row["classification"] in {"exact", "probable"}
    }
    missing_seed_ids = sorted(set(seed_ids) - {str(row["official_work_id"]) for row in report_rows})
    failed_with_candidates = sorted(set(failed_ids) & exact_or_probable)
    text_rescue_triage_candidates = [
        _text_rescue_triage_candidate(
            row,
            bootstrap_failure=failure_records_by_id.get(str(row["official_work_id"])),
        )
        for row in report_rows
        if row["official_work_id"] in failed_with_candidates
        and row["classification"] in {"exact", "probable"}
        and row["selected_candidate"] is not None
    ]
    review_report_ids = _extract_review_report_work_ids(review_report)
    review_report_ids_with_candidates = sorted(set(review_report_ids) & exact_or_probable)
    review_report_ids_missing = sorted(
        set(review_report_ids) - {str(row["official_work_id"]) for row in report_rows}
    )

    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_role": "secondary_corroborating",
        "source_inventory": NZLII_SOURCE_INVENTORY,
        "coverage_warning": (
            "NZLII is a secondary corroborating source only. "
            "Official NZ Legislation records remain canonical unless manually reconciled."
        ),
        "official_record_count": len(official_records),
        "candidate_record_count": sum(len(group) for group in candidate_groups.values()),
        "seed_comparison": {
            "seed_work_id_count": len(seed_ids),
            "seed_ids_missing_from_official_records": missing_seed_ids,
        },
        "bootstrap_failure_comparison": {
            "bootstrap_failure_count": len(failed_ids),
            "failed_ids_with_exact_or_probable_nzlii_candidate": failed_with_candidates,
            "bootstrap_failure_records": [
                failure_records_by_id[work_id]
                for work_id in failed_ids
                if work_id in failure_records_by_id
            ],
        },
        "review_report_comparison": {
            "review_report_supplied": review_report is not None,
            "review_report_work_id_count": len(review_report_ids),
            "review_report_ids_with_exact_or_probable_nzlii_candidate": (
                review_report_ids_with_candidates
            ),
            "review_report_ids_missing_from_official_records": review_report_ids_missing,
        },
        "text_rescue_triage_candidates": text_rescue_triage_candidates,
        "classification_counts": classification_counts,
        "records": report_rows,
        "manual_review_candidates": manual_review_candidates,
    }


def write_nzlii_reconciliation_report(
    output_path: str | Path,
    official_records: Sequence[OfficialMetadataRecord | Mapping[str, Any]],
    candidate_groups: Mapping[str, Sequence[NZLIICandidateRecord | Mapping[str, Any]]],
    *,
    seed_work_ids: Sequence[str] | None = None,
    bootstrap_failure_ids: Sequence[str] | None = None,
    bootstrap_failure_records: Sequence[Mapping[str, Any]] | None = None,
    review_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report = build_nzlii_reconciliation_report(
        official_records,
        candidate_groups,
        seed_work_ids=seed_work_ids,
        bootstrap_failure_ids=bootstrap_failure_ids,
        bootstrap_failure_records=bootstrap_failure_records,
        review_report=review_report,
    )
    write_json(Path(output_path), report)
    return report


def _candidate_to_dict(
    candidate: NZLIICandidateRecord | None,
    *,
    classification: NZLIIMatchClassification | None = None,
) -> dict[str, Any] | None:
    if candidate is None:
        return None
    return {
        "url": candidate.url,
        "title": candidate.title,
        "date": candidate.date,
        "retrieved_at": candidate.retrieved_at,
        "content_hash": candidate.content_hash,
        "confidence": round(candidate.confidence, 3),
        "classification": classification or candidate.classification,
    }


def _text_rescue_triage_candidate(
    row: Mapping[str, Any],
    *,
    bootstrap_failure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = row["selected_candidate"]
    triage_row = {
        "official_work_id": row["official_work_id"],
        "official_version_id": row["official_version_id"],
        "official_title": row["official_title"],
        "official_date": row["official_date"],
        "classification": row["classification"],
        "confidence": row["confidence"],
        "fallback_status": "secondary_text_rescue_candidate_review_required",
        "source_role": "secondary_corroborating",
        "retrieval_method": "nzlii_text_rescue_candidate",
        "canonical_promotion_allowed": False,
        "review_required": True,
        "reason": (
            "Official bootstrap retrieval failed and NZLII has an exact/probable "
            "candidate. Treat as non-canonical review evidence only."
        ),
        "selected_candidate": candidate,
    }
    if bootstrap_failure is not None:
        triage_row["bootstrap_failure"] = dict(bootstrap_failure)
    return triage_row


def _extract_record_id(row: Mapping[str, Any]) -> str:
    return str(
        row.get("work_id")
        or row.get("record_id")
        or row.get("stable_id")
        or row.get("official_work_id")
        or ""
    ).strip()


def _failure_records_by_id(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    failures: dict[str, dict[str, Any]] = {}
    for record in records:
        work_id = _extract_record_id(record)
        if work_id:
            failures[work_id] = dict(record)
    return failures


def _extract_review_report_work_ids(review_report: Mapping[str, Any] | None) -> list[str]:
    if review_report is None:
        return []
    work_ids: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            work_id = _extract_record_id(value)
            if work_id:
                work_ids.add(work_id)
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for key in (
        "failed_records",
        "missing_records",
        "manual_review_candidates",
        "records",
        "sync_failures",
        "validation_failures",
    ):
        if key in review_report:
            visit(review_report[key])
    return sorted(work_ids)
