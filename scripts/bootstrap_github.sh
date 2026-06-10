#!/usr/bin/env bash
set -euo pipefail

# Create and configure a fresh GitHub repository for the NZ legislation corpus pipeline.
# Run from the repository root after installing and authenticating the GitHub CLI:
#   gh auth login

REPO_NAME="${REPO_NAME:-corpus-legislation-nz}"
REPO_VISIBILITY="${REPO_VISIBILITY:-${VISIBILITY:-private}}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
DESCRIPTION="${REPO_DESCRIPTION:-API-first NZ legislation corpus pipeline: NZ API -> optimized Parquet -> Hugging Face/Xet -> annual Zenodo DOI snapshots.}"
GITHUB_OWNER="${GITHUB_OWNER:-${REPO_OWNER:-${GH_OWNER:-}}}"
PROTECT_PRODUCTION="${PROTECT_PRODUCTION:-false}"
ALLOW_EXISTING="${ALLOW_EXISTING:-false}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo|--name)
      REPO_NAME="${2:?Missing value for $1}"; shift 2 ;;
    --owner)
      GITHUB_OWNER="${2:?Missing value for --owner}"; shift 2 ;;
    --public)
      REPO_VISIBILITY="public"; shift ;;
    --private)
      REPO_VISIBILITY="private"; shift ;;
    --internal)
      REPO_VISIBILITY="internal"; shift ;;
    --protect-production)
      PROTECT_PRODUCTION="true"; shift ;;
    --allow-existing)
      ALLOW_EXISTING="true"; shift ;;
    -h|--help)
      cat <<'HELP'
Usage: scripts/bootstrap_github.sh [--repo NAME] [--owner OWNER] [--public|--private|--internal] [--protect-production] [--allow-existing]

Environment variables can also be used: GITHUB_OWNER/REPO_OWNER/GH_OWNER, REPO_NAME,
REPO_VISIBILITY, HF_REPO_ID, ARCHIVE_CREATORS_JSON, NZ_LEGISLATION_API_KEY, HF_TOKEN, ZENODO_TOKEN, ZENODO_SANDBOX_TOKEN.
HELP
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI 'gh' is required. Install it, then run: gh auth login" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run: gh auth login" >&2
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required." >&2
  exit 1
fi

case "$REPO_VISIBILITY" in
  public|private|internal) ;;
  *) echo "REPO_VISIBILITY must be public, private, or internal" >&2; exit 1 ;;
esac

OWNER="${GITHUB_OWNER:-$(gh api user --jq .login)}"
FULL_REPO="$OWNER/$REPO_NAME"

if gh repo view "$FULL_REPO" >/dev/null 2>&1 && [[ "$ALLOW_EXISTING" != "true" ]]; then
  echo "Repository already exists: $FULL_REPO" >&2
  echo "Refusing to push to an existing repository. Re-run with --allow-existing if this is intentional." >&2
  exit 3
fi

# Keep the source repo code-only. Local generated data must never be committed.
rm -rf data dist .pytest_cache .ruff_cache .mypy_cache .venv __pycache__
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true

if [ ! -d .git ]; then
  git init -b "$DEFAULT_BRANCH"
else
  git branch -M "$DEFAULT_BRANCH"
fi

git add .
if git diff --cached --quiet; then
  echo "No local changes to commit."
else
  git commit -m "Initial NZ legislation corpus pipeline"
fi

if gh repo view "$FULL_REPO" >/dev/null 2>&1; then
  echo "Repository already exists: $FULL_REPO"
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "https://github.com/$FULL_REPO.git"
  else
    git remote add origin "https://github.com/$FULL_REPO.git"
  fi
  git push -u origin "$DEFAULT_BRANCH"
else
  gh repo create "$FULL_REPO" \
    "--$REPO_VISIBILITY" \
    --source . \
    --remote origin \
    --push \
    --description "$DESCRIPTION" \
    --disable-wiki
fi

# Set low-maintenance repository defaults. Ignore failures because some settings are plan- or policy-dependent.
gh api --method PATCH "repos/$FULL_REPO" \
  -f has_wiki=false \
  -f delete_branch_on_merge=true \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=true >/dev/null || true

set_var() {
  local name="$1" value="$2"
  if [ -n "$value" ]; then
    gh variable set "$name" --repo "$FULL_REPO" --body "$value" >/dev/null
    echo "Set variable: $name"
  else
    echo "Skipped variable $name: no value provided"
  fi
}

set_secret() {
  local name="$1" value="$2"
  if [ -n "$value" ]; then
    printf '%s' "$value" | gh secret set "$name" --repo "$FULL_REPO" >/dev/null
    echo "Set secret: $name"
  else
    echo "Skipped secret $name: no value provided"
  fi
}

set_var HF_REPO_ID "${HF_REPO_ID:-$OWNER/corpus-legislation-nz}"
set_var DATA_DIR "${DATA_DIR:-data}"
set_var NZLC_SEARCH_TERMS "${NZLC_SEARCH_TERMS:-act,bill,regulation,order,notice}"
set_var NZLC_SEARCH_SORT_BY "${NZLC_SEARCH_SORT_BY:-most_recently_updated}"
set_var NZLC_SEARCH_FIELD "${NZLC_SEARCH_FIELD:-title}"
set_var NZLC_LEGISLATION_TYPES "${NZLC_LEGISLATION_TYPES:-act,bill,secondary_legislation,amendment_paper}"
set_var NZLC_LEGISLATION_STATUS "${NZLC_LEGISLATION_STATUS:-}"
set_var NZLC_PUBLISHER "${NZLC_PUBLISHER:-}"
DEFAULT_ARCHIVE_CREATORS_JSON="$(printf '[{"name":"%s"}]' "$OWNER")"
set_var ARCHIVE_CREATORS_JSON "${ARCHIVE_CREATORS_JSON:-$DEFAULT_ARCHIVE_CREATORS_JSON}"
set_var ARCHIVE_TITLE "${ARCHIVE_TITLE:-New Zealand Legislation Corpus}"
set_var ARCHIVE_LICENSE "${ARCHIVE_LICENSE:-cc-by-4.0}"
set_var ARCHIVE_PUBLISH "${ARCHIVE_PUBLISH:-false}"
set_var ZENODO_API_URL "${ZENODO_API_URL:-https://zenodo.org/api}"
set_var ZENODO_SANDBOX_API_URL "${ZENODO_SANDBOX_API_URL:-https://sandbox.zenodo.org/api}"
set_var ZENODO_DEPOSITION_ID "${ZENODO_DEPOSITION_ID:-}"

set_secret NZ_LEGISLATION_API_KEY "${NZ_LEGISLATION_API_KEY:-}"
set_secret HF_TOKEN "${HF_TOKEN:-}"
set_secret ZENODO_TOKEN "${ZENODO_TOKEN:-}"
set_secret ZENODO_SANDBOX_TOKEN "${ZENODO_SANDBOX_TOKEN:-}"

# Create deployment environments used by the annual archive workflow.
printf '{"wait_timer":0}' \
  | gh api --method PUT "repos/$FULL_REPO/environments/zenodo-sandbox" --input - >/dev/null || true
if [[ "$PROTECT_PRODUCTION" == "true" ]]; then
  USER_ID="$(gh api user --jq .id)"
  if printf '{"wait_timer":0,"reviewers":[{"type":"User","id":%s}],"deployment_branch_policy":null}' "$USER_ID"     | gh api --method PUT "repos/$FULL_REPO/environments/zenodo-production" --input - >/dev/null; then
    echo "Configured zenodo-production with the authenticated user as required reviewer."
  else
    echo "Could not configure required reviewers automatically; created zenodo-production without reviewer rules." >&2
    printf '{"wait_timer":0}' \
      | gh api --method PUT "repos/$FULL_REPO/environments/zenodo-production" --input - >/dev/null || true
  fi
else
  printf '{"wait_timer":0}' \
    | gh api --method PUT "repos/$FULL_REPO/environments/zenodo-production" --input - >/dev/null || true
fi

echo
cat <<SUMMARY
Created or updated: https://github.com/$FULL_REPO

Next manual hardening steps:
1. Open Settings -> Environments -> zenodo-production.
2. Add a required reviewer before allowing production Zenodo publication.
3. Open Settings -> Branches / Rulesets and require the 'Tests' workflow before merging.
4. Create the Hugging Face dataset repo if it does not exist:
   HF_TOKEN=... HF_REPO_ID=${HF_REPO_ID:-$OWNER/corpus-legislation-nz} ./scripts/create_huggingface_dataset_repo.sh
5. Test the workflow manually: Actions -> Hugging Face live sync -> Run workflow with max_works=5 and min_seconds_between_requests=1.0.
SUMMARY
