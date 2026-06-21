from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str | None, default: list[str] | None = None) -> list[str]:
    if value is None or not value.strip():
        return default or []
    return [part.strip() for part in value.split(",") if part.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        env_ignore_empty=True,
        populate_by_name=True,
    )

    nz_api_key: str | None = Field(default=None, alias="NZ_LEGISLATION_API_KEY")
    nz_api_base_url: str = Field(
        default="https://api.legislation.govt.nz/v0",
        alias="NZ_LEGISLATION_API_BASE_URL",
    )
    output_dir: Path = Field(default=Path("data"), alias="NZLC_OUTPUT_DIR")
    search_terms: list[str] = Field(default_factory=list, alias="NZLC_SEARCH_TERMS")
    search_field: str = Field(default="title", alias="NZLC_SEARCH_FIELD")
    search_sort_by: str = Field(
        default="most_recently_updated",
        alias="NZLC_SEARCH_SORT_BY",
    )
    legislation_types: list[str] = Field(default_factory=list, alias="NZLC_LEGISLATION_TYPES")
    legislation_status: str | None = Field(default=None, alias="NZLC_LEGISLATION_STATUS")
    publisher: str | None = Field(default=None, alias="NZLC_PUBLISHER")
    per_page: int = Field(default=100, alias="NZLC_PER_PAGE")
    request_timeout_seconds: float = Field(
        default=30.0,
        alias="NZLC_REQUEST_TIMEOUT_SECONDS",
    )
    min_seconds_between_requests: float = Field(
        default=0.20,
        alias="NZLC_MIN_SECONDS_BETWEEN_REQUESTS",
    )
    max_retries: int = Field(default=5, alias="NZLC_MAX_RETRIES")
    rate_limit_low_watermark: int = Field(
        default=10,
        alias="NZLC_RATE_LIMIT_LOW_WATERMARK",
    )
    rate_limit_reset_padding_seconds: float = Field(
        default=2.0,
        alias="NZLC_RATE_LIMIT_RESET_PADDING_SECONDS",
    )
    rate_limit_max_sleep_seconds: float = Field(
        default=60.0,
        alias="NZLC_RATE_LIMIT_MAX_SLEEP_SECONDS",
    )
    hf_token: str | None = Field(default=None, alias="HF_TOKEN")
    hf_repo_id: str | None = Field(default=None, alias="HF_REPO_ID")
    hf_revision: str = Field(default="main", alias="HF_REVISION")
    zenodo_token: str | None = Field(default=None, alias="ZENODO_TOKEN")
    zenodo_api_url: str = Field(
        default="https://sandbox.zenodo.org/api",
        alias="ZENODO_API_URL",
    )
    zenodo_deposition_id: str | None = Field(
        default=None,
        alias="ZENODO_DEPOSITION_ID",
    )
    archive_title: str = Field(
        default="New Zealand Legislation Corpus",
        alias="ARCHIVE_TITLE",
    )
    archive_creators: list[dict[str, Any]] = Field(default_factory=list)
    archive_license: str = Field(default="cc-by-4.0", alias="ARCHIVE_LICENSE")
    archive_publish_default: bool = Field(default=False, alias="ARCHIVE_PUBLISH")
    pipeline_version: str = Field(default="local-dev", alias="GITHUB_SHA")

    @field_validator("output_dir", mode="before")
    @classmethod
    def resolve_output_dir(cls, v: Any) -> Path:
        if isinstance(v, str):
            return Path(v)
        if isinstance(v, Path):
            data_dir = os.getenv("DATA_DIR")
            if data_dir:
                return Path(data_dir)
            return v
        return Path("data")

    @field_validator("archive_creators", mode="before")
    @classmethod
    def parse_archive_creators(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                raise ValueError("ARCHIVE_CREATORS_JSON must be a JSON array")
            except Exception as exc:
                raise ValueError(f"Invalid ARCHIVE_CREATORS_JSON: {exc}") from exc
        return v

    @field_validator("search_terms", "legislation_types", mode="before")
    @classmethod
    def parse_csv_fields(cls, v: Any) -> Any:
        if isinstance(v, str):
            return _split_csv(v)
        return v or []

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
