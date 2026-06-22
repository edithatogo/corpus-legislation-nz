from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

NZLC_ENV_VARS = (
    "NZ_LEGISLATION_API_KEY",
    "NZ_LEGISLATION_API_BASE_URL",
    "NZLC_OUTPUT_DIR",
    "NZLC_SEARCH_TERMS",
    "NZLC_SEARCH_FIELD",
    "NZLC_SEARCH_SORT_BY",
    "NZLC_LEGISLATION_TYPES",
    "NZLC_LEGISLATION_STATUS",
    "NZLC_PUBLISHER",
    "NZLC_PER_PAGE",
    "NZLC_REQUEST_TIMEOUT_SECONDS",
    "NZLC_MIN_SECONDS_BETWEEN_REQUESTS",
    "NZLC_MAX_RETRIES",
    "NZLC_RATE_LIMIT_LOW_WATERMARK",
    "NZLC_RATE_LIMIT_MAX_SLEEP_SECONDS",
    "NZLC_RETRY_AFTER_FALLBACK_SECONDS",
    "NZLC_HF_DATASET_REPO",
    "NZLC_HF_TOKEN",
    "HF_TOKEN",
    "HF_HUB_TOKEN",
)


@pytest.fixture(autouse=True, scope="session")
def _isolate_settings_env() -> None:
    """Clear user-shell NZLC env vars so Settings() uses defaults during tests.

    Without this, a developer's exported NZLC_* values leak into the test
    process and trigger pydantic_settings parse errors on the CSV-style
    list fields.
    """
    for var in NZLC_ENV_VARS:
        os.environ.pop(var, None)


@pytest.fixture
def tmp_path() -> Path:
    """Provide a repo-local temporary directory for filesystem tests."""
    root = Path.cwd() / "test-tmp"
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / f".probe-{uuid.uuid4().hex}"
        probe.mkdir()
        probe.rmdir()
    except PermissionError:
        root = Path.cwd() / ".tmp" / "test-tmp"
        root.mkdir(parents=True, exist_ok=True)
    path = root / f"case-{uuid.uuid4().hex}"
    path.mkdir()
    return path
