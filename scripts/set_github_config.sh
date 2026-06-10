#!/usr/bin/env bash
set -euo pipefail

REPO_FULL_NAME="${1:-${GITHUB_REPOSITORY:-edithatogo/corpus-legislation-nz}}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required." >&2
  exit 2
fi
if ! gh repo view "$REPO_FULL_NAME" >/dev/null 2>&1; then
  echo "Repository not found or inaccessible: $REPO_FULL_NAME" >&2
  exit 2
fi

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 2
  fi
}

require_env NZ_LEGISLATION_API_KEY
require_env HF_TOKEN
require_env ZENODO_TOKEN

gh secret set NZ_LEGISLATION_API_KEY --repo "$REPO_FULL_NAME" --body "$NZ_LEGISLATION_API_KEY"
gh secret set HF_TOKEN --repo "$REPO_FULL_NAME" --body "$HF_TOKEN"
gh secret set ZENODO_TOKEN --repo "$REPO_FULL_NAME" --body "$ZENODO_TOKEN"

if [[ -n "${OSF_TOKEN:-}" ]]; then
  gh secret set OSF_TOKEN --repo "$REPO_FULL_NAME" --body "$OSF_TOKEN"
fi

gh variable set HF_REPO_ID --repo "$REPO_FULL_NAME" --body "${HF_REPO_ID:-${REPO_FULL_NAME%/*}/corpus-legislation-nz}"
gh variable set NZLC_SEARCH_TERMS --repo "$REPO_FULL_NAME" --body "${NZLC_SEARCH_TERMS:-act,bill,regulation,order,notice}"
gh variable set NZLC_SEARCH_SORT_BY --repo "$REPO_FULL_NAME" --body "${NZLC_SEARCH_SORT_BY:-most_recently_updated}"
gh variable set NZLC_SEARCH_FIELD --repo "$REPO_FULL_NAME" --body "${NZLC_SEARCH_FIELD:-title}"
gh variable set NZLC_LEGISLATION_TYPES --repo "$REPO_FULL_NAME" --body "${NZLC_LEGISLATION_TYPES:-act,bill,secondary_legislation,amendment_paper}"
gh variable set ARCHIVE_TITLE --repo "$REPO_FULL_NAME" --body "${ARCHIVE_TITLE:-New Zealand Legislation Corpus}"
gh variable set ARCHIVE_CREATORS_JSON --repo "$REPO_FULL_NAME" --body "${ARCHIVE_CREATORS_JSON:-[{\"name\":\"REPLACE ME\"}]}"
gh variable set ARCHIVE_LICENSE --repo "$REPO_FULL_NAME" --body "${ARCHIVE_LICENSE:-cc-by-4.0}"
gh variable set ZENODO_API_URL --repo "$REPO_FULL_NAME" --body "${ZENODO_API_URL:-https://zenodo.org/api}"
gh variable set ZENODO_SANDBOX_API_URL --repo "$REPO_FULL_NAME" --body "${ZENODO_SANDBOX_API_URL:-https://sandbox.zenodo.org/api}"
gh variable set ARCHIVE_PUBLISH --repo "$REPO_FULL_NAME" --body "${ARCHIVE_PUBLISH:-false}"

if [[ -n "${ZENODO_DEPOSITION_ID:-}" ]]; then
  gh variable set ZENODO_DEPOSITION_ID --repo "$REPO_FULL_NAME" --body "$ZENODO_DEPOSITION_ID"
fi

echo "GitHub secrets and variables configured for $REPO_FULL_NAME"
