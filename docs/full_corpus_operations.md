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

After downloading a workflow artifact, run the deterministic review gate:

```text
nzlc review-full-corpus-bootstrap --artifact-root path/to/downloaded-artifact
```

The command writes `generated/full-corpus-bootstrap/review_report.json` by
default and exits non-zero if required artifact files are missing, validation
failed, failed versions remain, the manifest hash is absent, manifest or
coverage record counts do not match `records.jsonl`, or missing text, missing
XML URL, or ephemeral identifier risk indicators require triage.

For period-level agent handoff, first generate period seeds:

```text
nzlc split-work-id-periods \
  --seed-work-ids seeds/work_ids.txt \
  --output-dir seeds/periods \
  --manifest-path seeds/periods/manifest.json
```

The default annual recent/API-native boundary is an unverified planning
fallback. Supply `--api-boundary-year`, `--api-boundary-source`, and
`--api-boundary-verified` only after the boundary has been verified from
evidence. The generated period manifest includes `api_boundary_decision`; when
the default fallback is used, that field records the 2008 start year as
`planning_fallback_unverified` and carries a warning against treating it as an
API-native coverage claim. Use `.github/workflows/full_corpus_period_bootstrap.yml`
to run one period and upload a checkpoint artifact for agent review.

## Track 08 - Full Hugging Face upload

Workflow: `.github/workflows/full_corpus_hf_upload.yml`

First run with `upload_confirmed=false` to produce a review artifact. Pass the
completed Track 07 `bootstrap_run_id` when publishing a full-bootstrap artifact;
the workflow downloads `full-corpus-bootstrap-download` into the workspace root
so the artifact's `data/` tree remains intact. Without `bootstrap_run_id`, the
workflow restores the current live HF state and should be treated as a review
or maintenance check, not proof of a new full corpus.

The workflow stages the dataset card, validates the corpus, builds the manifest
and coverage report, then runs:

```text
nzlc review-full-corpus-bootstrap --artifact-root data
```

The upload step is reachable only after that review gate passes. The review
artifact includes `generated/full-corpus-bootstrap/review_report.json` alongside
`records.jsonl`, `README.md`, manifests, and `_state/`.

After review, rerun with `upload_confirmed=true` and the completed Track 07
`bootstrap_run_id`. Confirmed full upload fails closed when `bootstrap_run_id`
is empty, so the live partial/API-discovery dataset cannot be republished as a
full-corpus upload by mistake. The upload step calls `uv run nzlc hf-upload`;
the following verification step downloads the remote manifest and compares it
with the local manifest.

## Track 09 - Scheduled live sync

Workflow: `.github/workflows/hf_sync.yml`

The workflow remains the daily maintenance loop for the live dataset. Scheduled
runs use the configured schedule max-works variable and restore the live HF
state before syncing. Restore is fail-closed: if the current live Hugging Face
state cannot be downloaded, the workflow stops before upload rather than
publishing an empty or partial local state.

Manual smoke runs can still be dispatched with conservative inputs. The
post-upload verification step checks that the remote
`manifests/latest_manifest.json` matches the local manifest after upload.
Routine runs upload `hf-sync-maintenance-evidence` containing sync state,
latest changes, latest manifest, and coverage report artifacts for review.

## Track 11 - Monthly full reconciliation

Workflow: `.github/workflows/monthly_full_reconciliation.yml`

The workflow runs monthly and can also be dispatched manually. It restores the live HF dataset, validates and summarizes baseline coverage, discovers or ingests a candidate seed, reconciles the candidate against `seeds/work_ids.txt`, and uploads a reconciliation artifact.

Use `run_full_sync=true` only after the reconciliation artifact has been
reviewed. Do not use monthly reconciliation for confirmed publication; use
Track 08 after reviewing the full sync validation, manifest, coverage, and
failed-version state.
Scheduled runs use safe defaults when manual inputs are absent: baseline seed
`seeds/work_ids.txt`, no discovery/sync work limit, `1.0` second request
pacing, and 25 GB minimum free disk.

Confirmed publication is intentionally disabled in this workflow. Monthly
reconciliation produces review artifacts and may run a full sync after review,
but live Hugging Face publication must go through Track 08
`.github/workflows/full_corpus_hf_upload.yml` using the reviewed artifact.

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
