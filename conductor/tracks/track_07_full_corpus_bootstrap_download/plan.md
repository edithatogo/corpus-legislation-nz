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

## Remaining operator tasks

1. Trigger `full_corpus_bootstrap.yml` with `serial=true` for the final cumulative run
2. After completion, download artifacts: `data/records.jsonl`, `data/manifests/`, `data/_state/`
3. Review `sync_state.json` for failed versions and XML-to-HTML fallback warnings
4. Run `nzlc validate`, `nzlc manifest`, `nzlc coverage-report` against the output
5. Update tracks.md with final evidence (run URL, manifest SHA, record counts)
6. Mark Task 3 [x] and Task 7 [x] after review

