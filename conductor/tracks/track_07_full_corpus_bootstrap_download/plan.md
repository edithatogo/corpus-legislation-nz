# Plan - Full Corpus Bootstrap Download

## Tasks
- [x] Confirm runner disk budget (docs/runtime_capacity_runbook.md: 25 GB min, 50 GB preferred).
- [x] Restore current Hugging Face state before incremental runs (merge_policy=restore_merge in workflow).
- [ ] Run full seed sync via GitHub Actions (68 batches of 500 work IDs each).
- [x] Use staged batches (pre-split in generated/historical-discovery-27313765016/batches/).
- [x] Preserve sync state after each batch (merge_policy=restore_merge).
- [x] Validate, manifest, coverage-report commands available and tested.
- [ ] Review missing text, XML URLs, failed versions, and ephemeral identifiers per batch.

## Current state

- `seeds/work_ids.txt` exists (33,693 work IDs, Track 04). Root blocker resolved.
- All 68 reviewed historical batch files exist in `seeds/reviewed/` (0001-0068).
- Historical batches 0001-0003 confirmed-uploaded to `edithatogo/corpus-legislation-nz-historical`.
- Batch 0004 no-upload triggered: run `27362894765`.
- Full live corpus sync (68 batches) must run via GitHub Actions (no local API key or disk).
- Expected 4-6 weeks of batched historical uploads at current pace.

## Batch 0001 no-upload evidence

- Reviewed batch path: `seeds/reviewed/historical-work-ids-0001.txt`.
- GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27316467370`.
- Result: success with `upload_confirmed=false`; no Hugging Face write.
- Validation/manifest/coverage completed for 4,737 restored/merged records.
- Initial sync state recorded 436 failed versions, mostly early local/imperial
  Act XML 404 responses.
- XML-to-HTML fallback remediated the failures in rerun
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27330484544`.
- Confirmed batch 0001 upload passed in
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27331999831`.
- Confirmed batch 0001 sync state: 623 versions checked, 623 records added, 0
  records failed, 436 XML-to-HTML fallback warnings.
- Historical Hugging Face revision after upload:
  `dcc92964ef832c7e0bd2f904f88de523998304f2`.

## Batch 0002 evidence

- Reviewed batch path: `seeds/reviewed/historical-work-ids-0002.txt`.
- No-upload GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27344560156`.
- Confirmed batch 0002 upload passed in
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27347686841`.
- Confirmed batch 0002 sync state: 606 versions checked, 606 records added, 0
  records failed, 482 XML-to-HTML fallback warnings.
- Validation/manifest/coverage completed for 5,779 restored/merged records.
- Historical Hugging Face revision after upload:
  `bb425cb308410fac43095a30f88c9d92848a0eb8`.

## Batch 0003 evidence

- Reviewed batch path: `seeds/reviewed/historical-work-ids-0003.txt`.
- No-upload GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27351234418`.
- Confirmed batch 0003 upload passed in
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27354924156`.
- Confirmed batch 0003 sync state: 612 versions checked, 605 records added, 7
  records unchanged, 0 records failed, 487 XML-to-HTML fallback warnings.
- Validation/manifest/coverage completed for 6,384 restored/merged records.
- Historical Hugging Face revision after upload:
  `0cc4021cae106c0b9ae3722488faed21df3e578c`.


## Implementation automation added 2026-06-12

- Added `.github/workflows/full_corpus_bootstrap.yml` with manual batch splitting, disk-budget enforcement, HF restore, staged `nzlc sync`, validation, manifest, coverage-report, and artifact evidence.
- See `docs/full_corpus_operations.md` for the operator inputs and review
  sequence for this workflow.
- Parallel mode supports reviewed batch evidence; `serial=true` preserves one cumulative `data/` directory on a sufficiently large runner.
- Track remains `in_progress` until a full seed sync run produces and records final evidence.

## Full corpus bootstrap pilot run evidence (2026-06-12)

Run: `27396415830` (triggered via `gh workflow run`)
- Inputs: `batch_size=500`, `start_batch=1`, `end_batch=1`, `min_seconds_between_requests=1.0`, `serial=false`, `max_parallel=1`, `max_works=none`
- Plan job: completed (12s) with batch_count=1 for 500 work IDs
- Batch 0001 job: ran from 05:24:07Z to 10:38:47Z (5h14m40s)
  - Sync bootstrap batch step: 05:24:18Z to 10:38:46Z (5h14m28s)
  - Validate, manifest, and coverage-report: completed
  - Upload batch bootstrap artifact: completed
  - Batch summary: completed
- Serial job: skipped (serial=false)

### Sync performance analysis

500 work IDs (batch_0001: early imperial acts 1539-1730) took 5h14m at 1.0s pacing.
This is ~37 seconds per work ID, far above the ~3s expected from pacing alone.

Root cause: NZ Legislation API rate limiting. The `_sleep_for_low_quota` method
triggers when `X-RateLimit-Remaining` drops below `rate_limit_low_watermark=10`,
sleeping for `reset_time / remaining` seconds per call. Once quota is depleted,
the client waits for the full quota reset window (typically 1 hour) before
continuing, causing the exponential slowdown.

### Recommendation for full 68-batch run

1. Use `serial=true` with one cumulative data directory (24h runner timeout, 50GB+ disk)
2. Set `min_seconds_between_requests=0.5` for initial batches, then reduce to 0.2
   after confirming no 429/403 rate limiting
3. Expected wall-clock time: 8-15 hours for the full 33,693 work IDs at 0.5s pacing
   with observed API latency
4. Monitor `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers; if quota
   exhaustion is frequent, contact NZ Legislation API support for a higher tier
5. Alternative: process through the historical bootstrap workflow
   (`historical_hf_upload.yml`) which has been proven at 500-work scale with
   batches 0001-0003

## Code improvements applied 2026-06-13

The following production-hardening changes were made to support reliable 68-batch processing:

### Critical: quota sleep cap (`config.py`, `nz_api.py`)

Added `rate_limit_max_sleep_seconds=60.0` to cap `_sleep_for_low_quota`. Previously,
a quota-exhausted API key with `remaining=1` and `reset=3600s` could sleep 30+ minutes
per work ID (~1800s). The cap limits the maximum individual sleep to 60s, preventing
multi-hour stalls while still respecting the API quota system.

### Logging guard: `_download_first_available_format` (`cli.py`)

Added empty-content detection: if `download_url` returns zero bytes, the code now
raises an exception, triggering the XML->HTML fallback path instead of silently
returning empty content.

### Seed file warning: `_load_seed_work_ids` (`cli.py`)

Added a log warning when the seed work-IDs file exists but contains zero usable
(non-comment, non-empty) lines, preventing silent batch processing of empty batches.

### Serial mode progress tracking (`.github/workflows/full_corpus_bootstrap.yml`)

Added batch-level progress counters (`Processing batch 17/68`) to the serial batch
loop, providing real-time monitoring for the ~8-15 hour cumulative run.

### Extended test coverage

- **Rate limit tests** (`test_nz_api.py`): 9 new tests covering capped quota sleep,
  `_retry_after_seconds` invalid header fallback, `download_url` retries on 429/403/5xx,
  quota pause in download path, missing/expired header edge cases.
- **Download fallback tests** (`test_cli_download.py`): 5 new tests for
  `_download_first_available_format` covering XML success, XML->HTML fallback, both fail,
  HTML-only, and no formats available.
- **Coverage report tests** (`test_cli_coverage.py`): 3 new tests for empty corpus,
  multi-type records with risk indicators, and history append.
- **HF sync test** (`test_hf_sync.py`): prune stale paths test added.

All 65 tests pass; ruff lint clean.

## Test environment isolation applied 2026-06-16

After merging the 2026-06-13 hardening, the full pytest run on a developer
workstation exposed 34 pre-existing failures caused by user-shell `NZLC_*`
environment variables leaking into the test process and tripping
`pydantic_settings` list-field validation. These failures were independent of
the hardening work and surfaced only when the developer's shell exported
`NZLC_SEARCH_TERMS=law,act,...` style CSV values.

### Fix: tests/conftest.py autouse session fixture

Added a session-scoped autouse fixture (`_isolate_settings_env`) that pops the
known `NZLC_*`, `NZ_LEGISLATION_*`, `HF_TOKEN`, and `HF_HUB_TOKEN` env vars
before any test runs, so `Settings()` resolves to its declared defaults.

### Result

- `uv run pytest -q -p no:cacheprovider tests` reports **122 passed** in ~8s.
- `uv run ruff check tests/conftest.py` reports **All checks passed**.
- 5 pre-existing ruff findings in `embeddings.py` (D205/D212/D400/D415) and
  `utils.py` (I001) are unrelated to this track and remain on `main`; they are
  tracked separately.


## Remaining operator tasks

1. Trigger `full_corpus_bootstrap.yml` with `serial=true` for the final cumulative run
2. After completion, download artifacts: `data/records.jsonl`, `data/manifests/`, `data/_state/`
3. Review `sync_state.json` for failed versions and XML-to-HTML fallback warnings
4. Run `nzlc validate`, `nzlc manifest`, `nzlc coverage-report` against the output
5. Update tracks.md with final evidence (run URL, manifest SHA, record counts)
6. Mark Task 3 [x] and Task 7 [x] after review

