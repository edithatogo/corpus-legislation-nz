#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install from https://docs.astral.sh/uv/ then rerun." >&2
  exit 1
fi

rm -rf data dist
uv sync --extra dev --frozen
ARCHIVE_CREATORS_JSON='[{"name":"Local Smoke Test"}]' uv run nzlc smoke-fixture --output-dir data
NZLC_OUTPUT_DIR=data uv run nzlc validate
NZLC_OUTPUT_DIR=data uv run nzlc manifest
NZLC_OUTPUT_DIR=data uv run nzlc coverage-report
NZLC_OUTPUT_DIR=data uv run nzlc archive --year "$(date -u +%Y)" --output-dir dist/archive
uv run ruff check .
uv run pytest -q

echo "Local smoke test passed."
