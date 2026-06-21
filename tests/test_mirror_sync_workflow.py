from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "mirror_sync.yml"
OSF_POLICY = ROOT / "docs" / "osf-optional-mirror-policy.md"
MIRROR_RUNBOOK = ROOT / "docs" / "mirror-sync-setup.md"


def test_mirror_sync_supports_multiple_secondary_remotes() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "GIT_MIRROR_URLS" in workflow
    assert 'MIRROR_URLS="${GIT_MIRROR_URLS:-$GIT_MIRROR_URL}"' in workflow
    assert "while IFS= read -r MIRROR_URL" in workflow
    assert 'git remote add "$REMOTE_NAME" "$MIRROR_URL"' in workflow
    assert 'git push --force --prune "$REMOTE_NAME" "HEAD:${GITHUB_REF}"' in workflow


def test_mirror_sync_rejects_non_ssh_urls_per_remote() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'case "$MIRROR_URL" in' in workflow
    assert "Each mirror URL must be an SSH remote" in workflow


def test_mirror_sync_fails_when_any_mirror_command_fails() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "set -euo pipefail" in workflow
    assert 'done <<< "$MIRROR_URLS"' in workflow
    assert 'printf \'%s\\n\' "$MIRROR_URLS" | while' not in workflow


def test_osf_policy_uses_existing_validator_command() -> None:
    policy = OSF_POLICY.read_text(encoding="utf-8")

    assert "python scripts/check_osf_optional_policy.py" in policy
    assert "validate_osf_optional_mirror_policy.py" not in policy


def test_mirror_setup_runbook_documents_secret_and_verification_contract() -> None:
    runbook = MIRROR_RUNBOOK.read_text(encoding="utf-8")

    assert "GIT_MIRROR_URLS" in runbook
    assert "GIT_MIRROR_SSH_PRIVATE_KEY" in runbook
    assert "gh secret set GIT_MIRROR_URLS" in runbook
    assert "gh secret set GIT_MIRROR_SSH_PRIVATE_KEY" in runbook
    assert "gh workflow run mirror_sync.yml" in runbook
    assert "gh run view" in runbook
    assert "Do not commit mirror private keys" in runbook
