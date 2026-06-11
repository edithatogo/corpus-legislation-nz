# Runtime capacity, batching, and resume runbook

This runbook defines the operating defaults for the first full bootstrap and later large maintenance runs.

## Current capacity decision

Run the first full bootstrap on a controlled local or self-hosted runner, not on GitHub Actions. Use GitHub Actions for daily/latest maintenance after the first complete Hugging Face upload has been verified.

Reasons:

- The full work-id inventory is not available yet, so final API call count and corpus size are still unknown.
- GitHub-hosted runners have fixed runtime and disk limits that are awkward for an unproven first bootstrap.
- A local/self-hosted runner can preserve `data/_state/sync_state.json`, partial `records.jsonl`, raw content, and Parquet files between batches.

## Disk budget

Until the complete seed inventory exists, use a conservative minimum of 4x the final live corpus size on the bootstrap runner:

- raw files: 1x
- normalized JSONL and manifests: 0.25x to 0.5x
- Parquet partitions: 0.25x to 0.75x
- annual archive staging in `dist/archive`: 1x to 1.5x
- temporary upload/archive overhead and safety margin: 1x

For the expected 6 GB class corpus, reserve at least 25 GB free before starting. Prefer 50 GB free if embeddings or archive staging are enabled on the same runner. Record the actual before/after sizes in the track evidence once Track 07 has produced a real corpus.

Useful size checks:

```bash
du -sh data data/raw_xml data/parquet data/manifests dist/archive 2>/dev/null || true
```

On Windows PowerShell:

```powershell
Get-PSDrive -Name C
Get-ChildItem -LiteralPath data -Recurse -File | Measure-Object -Property Length -Sum
```

## Batch defaults

Start with small manual batches, then increase only after validation and upload behavior are clean:

- smoke: `--max-works 5`, `NZLC_MIN_SECONDS_BETWEEN_REQUESTS=1.0`
- pilot: `--max-works 50`, `NZLC_MIN_SECONDS_BETWEEN_REQUESTS=1.0`
- medium: seed-file chunks of 250 works, `NZLC_MIN_SECONDS_BETWEEN_REQUESTS=0.5`
- full: seed-file chunks of 500 to 1000 works, `NZLC_MIN_SECONDS_BETWEEN_REQUESTS=0.2` only after prior batches do not trigger 429/403 throttling

Prefer deterministic seed-file chunks over broad search terms for the first full bootstrap. Keep each chunk file under `seeds/batches/` or another ignored/operator-only location unless it becomes part of the public discovery contract.

Generate deterministic chunks from a reviewed seed inventory:

```bash
uv run nzlc split-work-id-batches \
  --seed-work-ids seeds/work_ids.txt \
  --output-dir seeds/batches \
  --batch-size 250 \
  --filename-prefix historical-work-ids
```

Review `seeds/batches/manifest.json` before running uploads. Record the
`seed_sha256`, batch filename, batch SHA-256, and batch index in the run
evidence. A batch manifest proves deterministic slicing; it does not prove full
coverage unless the source seed inventory has also been reconciled.

Before splitting a new historical candidate seed, reconcile it with the current
reviewed baseline:

```bash
uv run nzlc reconcile-work-ids \
  --baseline-work-ids seeds/work_ids.txt \
  --candidate-work-ids generated/historical-work-ids.candidate.txt \
  --report-path generated/historical-work-id-reconciliation.json \
  --merged-output-path generated/historical-work-ids.merged.txt
```

The reconciliation report is a review artifact, not a completeness proof by
itself. See `docs/historical_completeness_plan.md`.

Example staged run:

```bash
export NZLC_OUTPUT_DIR=data
export NZLC_MIN_SECONDS_BETWEEN_REQUESTS=1.0
uv run nzlc sync --seed-work-ids seeds/batches/batch-001.txt --allow-no-search-terms
uv run nzlc validate
uv run nzlc manifest
uv run nzlc coverage-report
```

Repeat with the next batch file only after validation passes.

For GitHub Actions historical uploads, prefer a reviewed batch file with remote
state restore:

```text
seed_work_ids_path=seeds/reviewed/historical-work-ids-0003.txt
merge_policy=restore_merge
max_works=none
upload_confirmed=false
```

Promote `seeds/reviewed/historical-work-ids-0003.txt` from the deterministic
batch artifact before using this input. Its generated source is
`generated/historical-discovery-27313765016/batches/historical-work-ids-0003.txt`.

After reviewing the no-upload artifact, rerun the same inputs with
`upload_confirmed=true`. Do not use `merge_policy=no_restore_incremental` for
an incremental confirmed upload. A fresh GitHub runner without restore has no
existing `records.jsonl`, `raw_xml/`, `parquet/`, or `_state/`; uploading that
partial folder would risk pruning previously published historical files.

## Resume behavior

The sync command preserves known version hashes in `data/_state/sync_state.json`. Do not delete `_state` during a multi-batch bootstrap. If a run stops mid-bootstrap, rerun the same batch first, then continue with the next batch after validation passes.

Expected behavior:

- unchanged versions remain recorded in `_state/sync_state.json`;
- `records.jsonl` is merged by stable ID unless `--replace` is explicitly passed;
- Parquet is rewritten only when records change or Parquet files are missing;
- generated manifests exclude `_state`, so local resume metadata does not change the public content hash by itself.

On GitHub-hosted runners, resume means restoring the historical Hugging Face
dataset into `NZLC_OUTPUT_DIR` before syncing the next reviewed seed batch.
The manual `historical_hf_upload.yml` workflow defaults to this behavior with
`merge_policy=restore_merge`.

## Hugging Face upload resume

`nzlc hf-upload` uses `hf upload-large-folder` when the CLI is available, with `HF_XET_HIGH_PERFORMANCE=1` by default. If an upload is interrupted, rerun the same command after confirming `HF_TOKEN`, `HF_REPO_ID`, and `NZLC_OUTPUT_DIR` still point to the same dataset and local corpus.

Before rerunning, rebuild and compare the manifest:

```bash
uv run nzlc manifest
uv run nzlc hf-upload
```

If the remote manifest content hash already matches the local content hash, the upload command skips without rewriting the dataset unless `--force` is used.

## Cleanup after upload

Clean generated data only after the Hugging Face dataset has been re-downloaded or queried and the local manifest hash matches the remote/public manifest.

Do not delete Git-tracked files. Safe generated paths are:

- `data/`
- `dist/archive/`
- `.hf_cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.ty_cache/`
- `test-tmp/`

On Windows, resolve the target path before deleting and verify it is inside the repository root. Prefer moving a generated directory to a dated quarantine folder first if there is any uncertainty.

## GitHub Actions timeout fallback

If a full bootstrap exceeds GitHub-hosted Actions runtime:

1. Stop using GitHub-hosted runners for first bootstrap.
2. Continue locally or on a self-hosted runner using the same `data/` directory.
3. Upload to Hugging Face after each validated chunk if disk pressure is high.
4. Keep GitHub Actions on daily/latest maintenance only until the full corpus is published and verified.
5. Record the final disk usage, elapsed time, batch size, pacing, and first successful Hugging Face revision in the track evidence.
