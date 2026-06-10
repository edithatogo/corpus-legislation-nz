from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _split_csv(value: str | None, default: list[str] | None = None) -> list[str]:
    if value is None or not value.strip():
        return default or []
    return [part.strip() for part in value.split(",") if part.strip()]


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    nz_api_key: str | None
    nz_api_base_url: str
    output_dir: Path
    search_terms: list[str]
    search_field: str
    search_sort_by: str
    legislation_types: list[str]
    legislation_status: str | None
    publisher: str | None
    per_page: int
    request_timeout_seconds: float
    min_seconds_between_requests: float
    max_retries: int
    rate_limit_low_watermark: int
    rate_limit_reset_padding_seconds: float
    hf_token: str | None
    hf_repo_id: str | None
    hf_revision: str
    zenodo_token: str | None
    zenodo_api_url: str
    zenodo_deposition_id: str | None
    archive_title: str
    archive_creators: list[dict[str, Any]]
    archive_license: str
    archive_publish_default: bool
    pipeline_version: str

    @classmethod
    def from_env(cls) -> Settings:
        creators_raw = os.getenv("ARCHIVE_CREATORS_JSON", "[]")
        try:
            creators = json.loads(creators_raw)
            if not isinstance(creators, list):
                raise ValueError("ARCHIVE_CREATORS_JSON must be a JSON array")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid ARCHIVE_CREATORS_JSON: {exc}") from exc

        return cls(
            nz_api_key=os.getenv("NZ_LEGISLATION_API_KEY"),
            nz_api_base_url=os.getenv(
                "NZ_LEGISLATION_API_BASE_URL", "https://api.legislation.govt.nz/v0"
            ),
            output_dir=Path(os.getenv("NZLC_OUTPUT_DIR", os.getenv("DATA_DIR", "data"))),
            search_terms=_split_csv(os.getenv("NZLC_SEARCH_TERMS"), default=[]),
            search_field=os.getenv("NZLC_SEARCH_FIELD", "title"),
            search_sort_by=os.getenv("NZLC_SEARCH_SORT_BY", "most_recently_updated"),
            legislation_types=_split_csv(os.getenv("NZLC_LEGISLATION_TYPES"), default=[]),
            legislation_status=os.getenv("NZLC_LEGISLATION_STATUS") or None,
            publisher=os.getenv("NZLC_PUBLISHER") or None,
            per_page=int(os.getenv("NZLC_PER_PAGE", "100")),
            request_timeout_seconds=float(os.getenv("NZLC_REQUEST_TIMEOUT_SECONDS", "30")),
            min_seconds_between_requests=float(
                os.getenv("NZLC_MIN_SECONDS_BETWEEN_REQUESTS", "0.20")
            ),
            max_retries=int(os.getenv("NZLC_MAX_RETRIES", "5")),
            rate_limit_low_watermark=int(os.getenv("NZLC_RATE_LIMIT_LOW_WATERMARK", "10")),
            rate_limit_reset_padding_seconds=float(
                os.getenv("NZLC_RATE_LIMIT_RESET_PADDING_SECONDS", "2.0")
            ),
            hf_token=os.getenv("HF_TOKEN"),
            hf_repo_id=os.getenv("HF_REPO_ID"),
            hf_revision=os.getenv("HF_REVISION", "main"),
            zenodo_token=os.getenv("ZENODO_TOKEN"),
            zenodo_api_url=os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api"),
            zenodo_deposition_id=os.getenv("ZENODO_DEPOSITION_ID") or None,
            archive_title=os.getenv("ARCHIVE_TITLE", "New Zealand Legislation Corpus"),
            archive_creators=creators,
            archive_license=os.getenv("ARCHIVE_LICENSE", "cc-by-4.0"),
            archive_publish_default=_bool_env("ARCHIVE_PUBLISH", False),
            pipeline_version=os.getenv("GITHUB_SHA", "local-dev"),
        )

    @property
    def raw_xml_dir(self) -> Path:
        return self.output_dir / "raw_xml"

    @property
    def parquet_dir(self) -> Path:
        return self.output_dir / "parquet"

    @property
    def manifests_dir(self) -> Path:
        return self.output_dir / "manifests"

    @property
    def state_dir(self) -> Path:
        return self.output_dir / "_state"

    @property
    def records_jsonl_path(self) -> Path:
        return self.output_dir / "records.jsonl"

    @property
    def sync_state_path(self) -> Path:
        return self.state_dir / "sync_state.json"


def require(value: str | None, name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required configuration: {name}")
    return value
