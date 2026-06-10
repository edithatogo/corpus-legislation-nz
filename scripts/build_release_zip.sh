#!/usr/bin/env bash
set -euo pipefail

version="${1:-v0.5}"
out="${2:-/tmp/corpus-legislation-nz-${version}.zip}"

rm -rf data dist .pytest_cache .ruff_cache .mypy_cache .venv .hf_cache
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true

zip -r "$out" . \
  -x '.git/*' \
  -x 'data/*' \
  -x 'dist/*' \
  -x '.venv/*' \
  -x '.hf_cache/*' \
  -x '__pycache__/*' \
  -x '*/__pycache__/*' \
  -x '*.pyc' \
  -x '.pytest_cache/*' \
  -x '.ruff_cache/*' \
  -x '.mypy_cache/*'

echo "$out"
