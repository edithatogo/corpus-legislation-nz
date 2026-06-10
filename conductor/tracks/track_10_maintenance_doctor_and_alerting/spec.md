# Spec - Maintenance Doctor And Alerting

## Status
ready

## Goal
surface token, API, and dependency failures before they affect the live corpus.

## Acceptance Criteria
- Doctor workflow passes once with live secrets.
- Failure notification path is known.
- Maintainer has a weekly check routine.

## Evidence to Record
- Doctor workflow run URL.
- Notification destination.
- Any follow-up alerting issue.

## Evidence Recorded

- Local doctor workflow check on 2026-06-07:
  - `.github/workflows/doctor.yml`: present.
  - Schedule: `42 15 * * 0` weekly.
  - Manual dispatch is configured.
  - Permissions are read-only for contents.
  - The workflow runs `uv run nzlc doctor --network`.
  - The workflow passes `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, `HF_REPO_ID`, `ZENODO_TOKEN`, `ZENODO_API_URL`, and `ARCHIVE_CREATORS_JSON` from GitHub secrets/variables.
- Local non-network doctor command on 2026-06-07:
  - Command: `uv run --no-cache nzlc doctor`.
  - `NZ_LEGISLATION_API_KEY`: warning, not configured.
  - `HF_REPO_ID`: warning, not configured.
  - `HF_TOKEN`: warning, not configured.
  - `ZENODO_TOKEN`: warning, not configured.
  - `ARCHIVE_CREATORS_JSON`: warning, not configured.
  - `output_dir`: `data`.
  - `data/` remained absent, so this local non-network check did not mutate corpus data.
- Maintenance and security configuration reviewed on 2026-06-07:
  - `.github/dependabot.yml`: weekly updates for GitHub Actions, uv, and pre-commit.
  - `.github/workflows/codeql.yml`: Python CodeQL on push, pull request, and weekly schedule.
  - `.github/workflows/scorecard.yml`: OpenSSF Scorecard on public repositories, schedule, branch protection rule, and manual dispatch.
  - `docs/maintenance_runbook.md`: weekly check routine includes doctor workflow, live sync summary, and Dependabot PRs.
- Alerting decision:
  - Do not add webhook or issue creation yet. Use GitHub Actions default workflow notifications until the repository exists and the first live doctor failure mode is observed.

## Blocked Items

- Cannot confirm the doctor workflow is enabled on the default branch until a GitHub remote/repository is configured and pushed.
- Cannot produce a doctor workflow run URL until GitHub Actions is available.
- Cannot pass live network doctor until Track 02 secrets/variables are configured.
- Cannot confirm maintainer notification delivery until a GitHub Actions run has completed under the target repository settings.
