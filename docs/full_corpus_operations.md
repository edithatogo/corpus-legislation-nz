# Full corpus operations

This runbook covers the critical path from full bootstrap download through live publication, scheduled maintenance, and monthly reconciliation.

## Guardrails

- Full bootstrap and full upload operations require the live Hugging Face repository variable `HF_REPO_ID`, `HF_TOKEN`, and `NZ_LEGISLATION_API_KEY`.
- Workflows fail before API work if the runner has less than 25 GB free disk by default. Use a larger self-hosted runner if needed.
- Full upload workflows default to no-upload review mode. Set `upload_confirmed=true` only after reviewing validation, manifest, coverage, and sync-state artifacts.
- The live dataset remains the operational dataset at `edithatogo/corpus-legislation-nz`. Historical publication continues to use `edithatogo/corpus-legislation-nz-historical`.

## Track 07 - Full corpus bootstrap download

Workflow: `.github/workflows/full_corpus_bootstrap.yml`

Recommended first run is parallel no-upload review:

```text
seed_work_ids_path=seeds/work_ids.txt
batch_size=500
start_batch=1
end_batch=68
merge_policy=restore_merge
min_seconds_between_requests=1.0
max_parallel=2
serial=false
max_works=none
```

Use `serial=true` only on a runner with enough disk and runtime to preserve one cumulative `data/` directory across all batches. The serial mode is the closest workflow equivalent to a full local bootstrap download.

Review each batch artifact for:

- `_state/sync_state.json` failed-version warnings;
- `data/manifests/validation_report.json`;
- `data/manifests/latest_manifest.json`;
- `data/manifests/coverage_report.json`;
- record counts by type, status, and year.

## Track 08 - Full Hugging Face upload

Workflow: `.github/workflows/full_corpus_hf_upload.yml`

First run with `upload_confirmed=false` to produce a review artifact. The workflow restores the current live HF state, validates the local corpus, stages the dataset card, builds the manifest and coverage report, and uploads the review artifact.

After review, rerun with `upload_confirmed=true`. The upload step calls `uv run nzlc hf-upload`; the following verification step downloads the remote manifest and compares it with the local manifest.

## Track 09 - Scheduled live sync

Workflow: `.github/workflows/hf_sync.yml`

The workflow remains the daily maintenance loop for the live dataset. Scheduled runs use the configured schedule max-works variable and restore the live HF state before syncing. Manual smoke runs can still be dispatched with conservative inputs. The post-upload verification step checks that the remote `manifests/latest_manifest.json` matches the local manifest after upload.

## Track 11 - Monthly full reconciliation

Workflow: `.github/workflows/monthly_full_reconciliation.yml`

The workflow runs monthly and can also be dispatched manually. It restores the live HF dataset, validates and summarizes baseline coverage, discovers or ingests a candidate seed, reconciles the candidate against `seeds/work_ids.txt`, and uploads a reconciliation artifact.

Use `run_full_sync=true` only after the reconciliation artifact has been reviewed. Use `upload_confirmed=true` only after the full sync validation, manifest, coverage, and failed-version state have been reviewed.

## Evidence to record after completion

Record the following in the relevant Conductor track notes:

- workflow run URLs;
- seed SHA-256 and batch manifest;
- total works attempted;
- total versions and records produced;
- failed or skipped version list;
- final manifest SHA-256;
- coverage report path;
- Hugging Face revision after upload;
- reconciliation added/removed work-ID counts;
- coverage deltas and maintenance notes.
