# Plan - Credential And Secret Inventory

## Tasks
- [ ] Confirm `NZ_LEGISLATION_API_KEY` exists and can call the NZ Legislation API.
- [ ] Confirm `HF_TOKEN` exists and has write access only to the intended Hugging Face dataset repository where possible.
- [ ] Confirm `HF_REPO_ID` is final.
- [ ] Confirm `ZENODO_TOKEN` exists for sandbox first.
- [x] Decide whether production Zenodo uses a separate token and required reviewer environment.
- [ ] Store GitHub secrets: `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, and `ZENODO_TOKEN`.
- [ ] Store GitHub variables: `HF_REPO_ID`, `NZLC_SEARCH_TERMS`, `NZLC_SEARCH_FIELD`, `NZLC_SEARCH_SORT_BY`, `NZLC_LEGISLATION_TYPES`, `ARCHIVE_CREATORS_JSON`, and archive metadata.
- [x] Run `uv run nzlc doctor` locally or through GitHub Actions.

## Current blocker

- Required credential values are not present in the local environment.
- The isolated repository has no GitHub remote, so `gh secret list` and secret/variable writes cannot resolve a target repository.
