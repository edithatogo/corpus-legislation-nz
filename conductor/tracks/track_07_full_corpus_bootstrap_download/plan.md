# Plan - Full Corpus Bootstrap Download

## Tasks
- [ ] Confirm enough local or runner disk space for raw files, Parquet,
  manifests, and temporary archive work.
- [ ] Restore current Hugging Face state before any incremental full run.
- [ ] Run full seed sync with conservative pacing.
- [ ] Use staged batches if the seed inventory is large or API limits are
  uncertain.
- [ ] Preserve sync state after each batch.
- [ ] Run `uv run nzlc validate`, `uv run nzlc manifest`, and
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
