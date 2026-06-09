# Hugging Face setup

This project uses Hugging Face Datasets as the live operational data hub. GitHub stores code and workflows; Hugging Face stores the evolving corpus.

## Target dataset repository

Recommended default:

```text
edithatogo/nz-legislation-corpus
```

This target is for the live partial/API-discovery corpus line. Historical corpus
pilots must not upload over it; see `docs/historical_publication_policy.md`.

Historical corpus target:

```text
edithatogo/nz-legislation-corpus-historical
```

The historical target is separate from the live dataset, following the same
separation pattern used for Hansard. Historical upload workflows must read the
repository variable `HF_HISTORICAL_REPO_ID` and must fail closed if that
variable is absent or points at `HF_REPO_ID`.

## What can be automated

The repository can be created and initialised through the Hugging Face API or CLI once `HF_TOKEN` is available. The included script creates the dataset repository, uploads a dataset card, sets `.gitattributes`, creates lightweight placeholder directories at repository root, and removes any older `data/...` bootstrap placeholders.

```bash
export HF_TOKEN="hf_..."
export HF_REPO_ID="edithatogo/nz-legislation-corpus"
export HF_PRIVATE="false"
./scripts/create_huggingface_dataset_repo.sh "$HF_REPO_ID"
```

For the historical dataset shell, use the historical repository variable as the
target:

```bash
export HF_TOKEN="hf_..."
export HF_HISTORICAL_REPO_ID="edithatogo/nz-legislation-corpus-historical"
export HF_PRIVATE="false"
./scripts/create_huggingface_dataset_repo.sh "$HF_HISTORICAL_REPO_ID"
```

The script is idempotent: rerunning it updates the metadata shell but does not upload corpus data.

## Remote repository layout

The Hugging Face repository is stored at repository root, not under an extra `data/` prefix:

```text
records.jsonl
parquet/
raw_xml/
manifests/
_state/
```

The GitHub workflow downloads that repository into a local `data/` working directory, so remote `manifests/latest_manifest.json` becomes local `data/manifests/latest_manifest.json`.

## What the GitHub workflow will do

The `hf_sync.yml` workflow will:

1. run the NZ Legislation API sync;
2. validate records;
3. write stable partitioned Parquet;
4. generate manifests and coverage reports;
5. upload the corpus folder to Hugging Face with `hf upload-large-folder`.

Scheduled runs are intentionally bounded by default so routine operations do not
start an unreviewed broad historical crawl. Unless overridden by repository
variables, `schedule` events use:

```text
NZLC_SCHEDULE_MAX_WORKS=5
NZLC_SCHEDULE_MIN_SECONDS_BETWEEN_REQUESTS=1.0
```

Manual `workflow_dispatch` runs can still pass explicit `max_works` and
`min_seconds_between_requests` inputs for smoke tests or reviewed larger runs.

## Manual historical upload workflow contract

Historical publication is a separate, manual-only path. It must not use the
live `hf_sync.yml` workflow and must not have a `schedule` trigger.

Before a historical upload workflow is run:

1. `HF_HISTORICAL_REPO_ID` must be configured as a GitHub repository variable
   or supplied as an explicit manual workflow input.
2. `HF_HISTORICAL_REPO_ID` must not be empty.
3. `HF_HISTORICAL_REPO_ID` must not equal `HF_REPO_ID`.
4. The workflow must fail before sync or upload if any of those checks fail.
5. The workflow must default to dry-run/no-upload behavior until Track 21 and
   Track 22 evidence has been reviewed.

Historical upload commands should set the upload target from
`HF_HISTORICAL_REPO_ID` only for the upload step. They must not silently fall
back to `HF_REPO_ID`, because `HF_REPO_ID` is reserved for the live
partial/API-discovery dataset.

A manual no-upload run is the expected first proof. It should generate or
restore historical working data, run validation/manifest/coverage checks, and
skip `uv run nzlc hf-upload`. A real upload run should require an explicit
manual input such as `upload_confirmed=true` after the historical target and
batch plan are approved.

## Why Xet matters

Hugging Face Hub uses Xet-backed storage for large files. Xet deduplicates content at the chunk level, so stable Parquet files with stable ordering reduce repeat upload cost. This is why the pipeline avoids daily monolithic archives and instead writes stable partitions.

## Required GitHub secret

```text
HF_TOKEN
```

The token needs write access to the dataset repo.

## Required GitHub variable

```text
HF_REPO_ID=edithatogo/nz-legislation-corpus
```

Required GitHub variable for future historical upload workflows:

```text
HF_HISTORICAL_REPO_ID=edithatogo/nz-legislation-corpus-historical
```

`HF_REPO_ID` and `HF_HISTORICAL_REPO_ID` must remain distinct. Historical
workflow code should reject `HF_HISTORICAL_REPO_ID=edithatogo/nz-legislation-corpus`
instead of uploading historical records over the live partial corpus.

## Recommended first checks

After creating the dataset repo:

```bash
uv run nzlc doctor --network
./scripts/first_run_local.sh
```

Then trigger the GitHub workflow manually once the GitHub repository exists and the NZ Legislation API key is configured.

## Manual fallback upload

```bash
export HF_TOKEN="hf_..."
export HF_REPO_ID="edithatogo/nz-legislation-corpus"
export HF_XET_HIGH_PERFORMANCE=1
uv run nzlc hf-upload
```

Do not use the fallback upload command for historical records unless the command
is explicitly pointed at `HF_HISTORICAL_REPO_ID` and the historical bootstrap
plan has been reviewed.

For historical data, prefer a no-upload validation run first:

```bash
export NZLC_OUTPUT_DIR="data-historical"
uv run nzlc validate
uv run nzlc manifest
uv run nzlc coverage-report
```

Only after review, point the upload target at the distinct historical repo:

```bash
test -n "$HF_HISTORICAL_REPO_ID"
test "$HF_HISTORICAL_REPO_ID" != "$HF_REPO_ID"
export HF_REPO_ID="$HF_HISTORICAL_REPO_ID"
export HF_XET_HIGH_PERFORMANCE=1
uv run nzlc hf-upload
```

## Do not manually edit data files

Manual edits in the Hugging Face dataset can be overwritten by the next successful pipeline run. Treat the GitHub pipeline as the source of truth for publication logic.
