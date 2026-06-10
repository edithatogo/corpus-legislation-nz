#!/usr/bin/env bash
set -euo pipefail

REPO_FULL_NAME="${1:-${GITHUB_REPOSITORY:-edithatogo/corpus-legislation-nz}}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
REQUIRED_TEST_CONTEXT="${REQUIRED_TEST_CONTEXT:-tests}"

warn() {
  echo "WARN: $*" >&2
}

gh api --method PATCH "repos/$REPO_FULL_NAME" \
  -f has_wiki=false \
  -f delete_branch_on_merge=true \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=true >/dev/null

gh api --method PUT "repos/$REPO_FULL_NAME/environments/zenodo-sandbox" >/dev/null || true
gh api --method PUT "repos/$REPO_FULL_NAME/environments/zenodo-production" >/dev/null || true

if ! gh api --method PUT "repos/$REPO_FULL_NAME/vulnerability-alerts" >/dev/null; then
  warn "Could not enable Dependabot alerts; check repository visibility, permissions, or plan."
fi

if ! gh api --method PATCH "repos/$REPO_FULL_NAME" \
  --input - >/dev/null <<'JSON'
{
  "security_and_analysis": {
    "secret_scanning": {
      "status": "enabled"
    },
    "secret_scanning_push_protection": {
      "status": "enabled"
    },
    "dependabot_security_updates": {
      "status": "enabled"
    }
  }
}
JSON
then
  warn "Could not enable one or more GitHub security analysis settings; check plan availability."
fi

if ! gh api --method PUT "repos/$REPO_FULL_NAME/branches/$DEFAULT_BRANCH/protection" \
  --input - >/dev/null <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["$REQUIRED_TEST_CONTEXT"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
then
  warn "Could not enable branch protection for $DEFAULT_BRANCH; confirm the branch exists and the tests check context is '$REQUIRED_TEST_CONTEXT'."
fi

cat <<EOF
Configured base hardening for $REPO_FULL_NAME.

Review required:
- Confirm Settings -> Environments -> zenodo-production has required reviewers.
- Confirm Settings -> Rulesets/Branches requires the '$REQUIRED_TEST_CONTEXT' check before merging.
- Confirm Settings -> Code security shows secret scanning, push protection, Dependabot alerts, and Dependabot security updates enabled or unavailable for the plan.
EOF
