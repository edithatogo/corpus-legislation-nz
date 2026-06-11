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
- [x] Record a dry-run/no-upload workflow run URL after merge.
- [ ] Record the first reviewed historical upload run URL
  only after Track 21 and Track 22 pass.

## Remaining external evidence

- First reviewed historical upload run URL remains pending until the historical
  target and batch plan are approved for writes.

## Dry-run proof

- Run URL:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27194196559`.
- Event: `workflow_dispatch`.
- Result: success.
- Inputs: `upload_confirmed=false`, `search_terms=act`,
  `legislation_status=none`, `legislation_types=act`, `max_pages=1`,
  `max_works=1`, `min_seconds_between_requests=1.0`.
- Upload behavior: `Upload to historical Hugging Face dataset` was skipped and
  dry-run artifacts were uploaded.

## Documentation evidence

- `docs/HUGGINGFACE_SETUP.md` defines the manual historical upload workflow
  contract and local fallback commands.
- `docs/historical_publication_policy.md` defines the fail-closed publication
  guardrails.
- `docs/historical_completeness_plan.md` defines the pre-upload seed
  reconciliation gate for historical completeness work.
- `conductor/tracks.md` records this Track 23 documentation/evidence slice.
- `.github/workflows/historical_hf_upload.yml` implements the manual workflow.

## Reviewed batch dry-run evidence

- Run URL:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27316467370`.
- Event: `workflow_dispatch`.
- Result: success.
- Inputs: `upload_confirmed=false`,
  `seed_work_ids_path=seeds/reviewed/historical-work-ids-0001.txt`,
  `merge_policy=restore_merge`, `max_pages=none`, `max_works=none`,
  `min_seconds_between_requests=0.5`.
- Upload behavior: `Upload to historical Hugging Face dataset` was skipped.
- Validation: 4,737 restored/merged records, `ok=true`.
- Manifest SHA-256:
  `19e5f5c8eb25307d170105659d20d459a42fea8668eb424223abc40b844bea51`.
- Stop condition: 436 failed versions were recorded in `_state/sync_state.json`,
  so confirmed upload of this batch remains pending failed-version triage.
