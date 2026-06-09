# Plan - Manual Historical Upload Workflow

## Tasks

- [x] Document the historical workflow as manual-only with no schedule.
- [x] Document the required distinct `HF_HISTORICAL_REPO_ID` target.
- [x] Document fail-closed behavior when `HF_HISTORICAL_REPO_ID` is absent.
- [x] Document fail-closed behavior when `HF_HISTORICAL_REPO_ID` equals `HF_REPO_ID`.
- [x] Document dry-run/no-upload behavior for first proof runs.
- [x] Record that historical uploads must not write to the live `HF_REPO_ID`
  dataset by default.
- [x] Parent workflow owner completes and verifies
  `.github/workflows/historical_hf_upload.yml`.
- [ ] Record a dry-run/no-upload workflow run URL after merge.
- [ ] Record the first reviewed historical upload run URL
  only after Track 21 and Track 22 pass.

## Remaining external evidence

- Dry-run/no-upload GitHub Actions run URL is pending execution on GitHub.
- First reviewed historical upload run URL remains pending until the historical
  target and batch plan are approved for writes.

## Documentation evidence

- `docs/HUGGINGFACE_SETUP.md` defines the manual historical upload workflow
  contract and local fallback commands.
- `docs/historical_publication_policy.md` defines the fail-closed publication
  guardrails.
- `conductor/tracks.md` records this Track 23 documentation/evidence slice.
- `.github/workflows/historical_hf_upload.yml` implements the manual workflow.
