# Spec - Full Corpus Bootstrap Download

## Status
in_progress

## Goal
download the full corpus into local `data/` using the proven discovery method and conservative pacing.

## Acceptance Criteria
- All seed works are attempted.
- Failed versions are recorded and triaged.
- Validation passes or documented exceptions are accepted.
- Coverage report is reviewed before any public completeness claim.

## Evidence to Record
- Total works attempted.
- Total versions and records produced.
- Failed or skipped version list.
- Final manifest hash.
- Coverage report path.

## Evidence Recorded

- Seed inventory: `seeds/work_ids.txt` now exists with 33,693 work IDs (search-derived, documented in Track 04).
- Pre-split batches: 68 batches of 500 work IDs each in `generated/historical-discovery-27313765016/batches/`.
- Historical batches 0001-0003 confirmed-uploaded to `edithatogo/corpus-legislation-nz-historical`.
- Batch 0004 no-upload triggered on 2026-06-11: run `27362894765`.
- Full live corpus sync requires GitHub Actions (no local API key; local disk ~7.5 GB free below 25 GB minimum).
- Runner disk budget documented in `docs/runtime_capacity_runbook.md`: minimum 25 GB, prefer 50 GB.

## Remaining Tasks

- Run remaining 68 historical batches through the no-upload â†’ review â†’ confirmed-upload cycle.
- Run full live corpus sync after historical batches are verified.
- Review validation, manifest, coverage evidence for each batch.
