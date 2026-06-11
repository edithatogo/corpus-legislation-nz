# Plan - Full Corpus Bootstrap Download

## Tasks
- [ ] Confirm enough local or runner disk space for raw files, Parquet,
  manifests, and temporary archive work.
- [ ] Restore current Hugging Face state before any incremental full run.
- [ ] Run full seed sync with conservative pacing.
- [ ] Use staged batches if the seed inventory is large or API limits are
  uncertain.
- [ ] Preserve sync state after each batch.
- [x] Run `uv run nzlc validate`, `uv run nzlc manifest`, and
  `uv run nzlc coverage-report`.
- [ ] Review missing text, missing XML URLs, failed versions, and ephemeral
  identifiers.

## Current blocker

- No authoritative `seeds/work_ids.txt` exists.
- The partial/API-discovery launch and historical bootstrap prove sync and
  publication mechanics, but they do not prove full corpus coverage.
- Final disk/runtime sizing cannot be confirmed until the authoritative full
  seed and expected archive size are known.
- Candidate historical seeds must be reconciled with `nzlc reconcile-work-ids`
  before they are promoted to `seeds/work_ids.txt` or split into upload batches.

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
