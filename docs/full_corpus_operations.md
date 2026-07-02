# Full corpus operations

This runbook covers the critical path from full bootstrap download through live publication, scheduled maintenance, and monthly reconciliation.

## Guardrails

- Full bootstrap and full upload operations require the live Hugging Face repository variable `HF_REPO_ID`, `HF_TOKEN`, and `NZ_LEGISLATION_API_KEY`.
- Workflows fail before API work if the runner has less than 25 GB free disk by default. Use a larger self-hosted runner if needed.
- Full upload workflows default to no-upload review mode. Set `upload_confirmed=true` only after reviewing validation, manifest, coverage, and sync-state artifacts.
- The live dataset remains the operational dataset at `edithatogo/corpus-legislation-nz`. Historical publication continues to use `edithatogo/corpus-legislation-nz-historical`.

## Track 07 - Full corpus bootstrap download

Workflow: `.github/workflows/full_corpus_bootstrap.yml`

Scheduled continuation workflow:
`.github/workflows/scheduled_full_corpus_bootstrap_batches.yml`

Recommended hosted-runner run is parallel shard review and merge:

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

Do not use `serial=true` for all 68 batches on GitHub-hosted runners. The
2026-06-21 full serial run was cancelled during the sync step after about six
hours, before validation, coverage, or artifact upload. Hosted runs should use
`serial=false`: each batch uploads a shard artifact, then the workflow's
`merge_batches` job assembles those shards into the standard
`full-corpus-bootstrap-download` artifact with a root `data/` tree.

Use `serial=true` only on a local or self-hosted runner with enough disk and
runtime to preserve one cumulative `data/` directory across all batches. The
serial mode is the closest workflow equivalent to a full local bootstrap
download, but it is not viable for the first all-batch hosted run.

For quota-safe continuation from batch 0024 onward, use the scheduled
dispatcher. The NZ Legislation API daily key limit is 10,000 requests, so the
dispatcher plans at 80% utilisation: 8,000 requests/day. With `batch_size=500`
and `requests_per_work_id_budget=8`, the request budget is 4,000 requests per
batch and the scheduled window is two batches per day. Batch 0024 evidence
supports this: it checked 500 works and 874 versions with 483 HTML fallbacks,
which gives an approximate upper-bound of 2,731 API requests. Two similar
batches remain comfortably under 8,000 requests/day; three fallback-heavy
batches could be close to the cap.

If a batch discovers API-visible records with no downloadable XML/HTML body,
`nzlc sync` defers those metadata-only versions into
`data/_state/metadata_only_deferred.jsonl` and reports `records_deferred` in
sync state. These deferred rows are not written to `records.jsonl`, so
validation continues to mean the corpus records present have usable text and
source provenance. Treat deferred rows as explicit gap evidence for official
website fallback and NZLII redundancy triage before claiming final completeness.

As of run `28566570973`, batches 0043-0052 have validated with this deferral
path. Batch 0051 preserved one deterministic not-found retrieval gap for
`secondary-legislation_pco-drafted_2001_007_en_2007-09-03` in
`metadata_only_deferred.jsonl` with reason `download_source_not_found`. The
scheduled continuation should start at batch 0053 to avoid repeating the
repaired window.

```text
start_batch=24
end_batch=68
schedule_start_date=2026-06-30
daily_request_limit=10000
utilization_percent=80
requests_per_work_id_budget=8
batch_size=500
min_seconds_between_requests=1.0
max_parallel=2
max_works=none
```

The dispatcher skips itself after the computed daily window passes batch 0068.
Manual dispatch of the dispatcher is useful for proving the calculation on a
branch, but scheduled runs only execute from GitHub's default branch.

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

If shard artifacts are downloaded outside GitHub Actions, assemble them with:

```text
nzlc merge-bootstrap-artifacts \
  --artifact-root path/to/full-corpus-batch-0001-download \
  --artifact-root path/to/full-corpus-batch-0002-download \
  --output-dir data
nzlc review-full-corpus-bootstrap --artifact-root data
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
