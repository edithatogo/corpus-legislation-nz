# Spec - Credential And Secret Inventory

## Status
blocked

## Goal
confirm all credentials and GitHub variables required for live corpus operations are present, scoped correctly, and stored in the right place.

## Acceptance Criteria
- `nzlc doctor` passes without exposing secret values.
- GitHub Actions has the required secrets and variables.
- Zenodo production publication remains approval-gated.

## Evidence to Record
- Redacted `nzlc doctor` result.
- GitHub repository variable names, not values.
- GitHub environment names and protection status.

## Evidence Recorded

- Local credential presence check on 2026-06-02:
  - `NZ_LEGISLATION_API_KEY`: absent.
  - `HF_TOKEN`: absent.
  - `HF_REPO_ID`: absent.
  - `ZENODO_TOKEN`: absent.
  - `ARCHIVE_CREATORS_JSON`: absent.
  - Optional search/archive variables checked in the local environment: absent.
- Local `nzlc doctor` result:
  - `NZ_LEGISLATION_API_KEY`: warning, not configured.
  - `HF_REPO_ID`: warning, not configured.
  - `HF_TOKEN`: warning, not configured.
  - `ZENODO_TOKEN`: warning, not configured.
  - `ARCHIVE_CREATORS_JSON`: warning, not configured.
  - `output_dir`: `data`.
- GitHub CLI:
  - Authenticated as `edithatogo`.
  - `gh secret list` failed with `no git remotes found`.
- Git repository:
  - Isolated local repository exists.
  - No GitHub remote is configured yet.
- Base repository / GitHub cross-check on 2026-06-02:
  - Parent Git root resolves to `C:/Users/60217257/OneDrive - Flinders`.
  - Obvious local base env file found: `.env.example` only; the file is OneDrive offline and no usable local `.env` credential file was found in bounded scans.
  - Documented default GitHub repo `edithatogo/nz-legislation-corpus-pipeline` is not resolvable by the authenticated GitHub account.
  - Likely base GitHub repo `edithatogo/nz-legislation` is accessible.
  - `edithatogo/nz-legislation` repo secrets contain only `CODECOV_TOKEN` and `NPM_TOKEN`; no `NZ_LEGISLATION_API_KEY`.
  - `edithatogo/nz-legislation` repo variables contain only `ENABLE_AUTOMATED_NPM_PUBLISH`; no NZ legislation corpus variables.
  - `edithatogo/nz-legislation` environments are `github-pages`, `prerelease`, and `stable`; environment secrets and variables are empty.
- Zenodo production decision:
  - Use `zenodo-sandbox` for test drafts.
  - Use `zenodo-production` with required reviewers for production drafts/publication.
  - Prefer a separate production `ZENODO_TOKEN` stored as an environment-scoped secret.
  - Keep production publication opt-in with `publish=true`.

## Blocked Items

- Cannot confirm live NZ Legislation API access until `NZ_LEGISLATION_API_KEY` is supplied.
- Base-repo checks did not locate an existing `NZ_LEGISLATION_API_KEY`.
- Cannot confirm Hugging Face write access until `HF_TOKEN` and final `HF_REPO_ID` are supplied.
- Cannot confirm Zenodo sandbox access until `ZENODO_TOKEN` is supplied.
- Cannot store GitHub secrets or variables until a GitHub remote/repository is configured.
