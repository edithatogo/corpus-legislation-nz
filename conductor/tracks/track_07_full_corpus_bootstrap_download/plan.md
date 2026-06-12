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
- Historical batches 0001-0003 confirmed-uploaded.
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
