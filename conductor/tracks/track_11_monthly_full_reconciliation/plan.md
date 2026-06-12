# Plan - Monthly Full Reconciliation

## Tasks
- [x] Define a monthly or quarterly full reconciliation cadence.
- [ ] Compare seed inventory, search discovery, and coverage report outputs.
- [ ] Add newly discovered work IDs to `seeds/work_ids.txt` with provenance.
- [ ] Rerun full sync in staged batches when the seed file changes materially.
- [ ] Review counts by legislation type, status, and year.

## Current blocker

- `docs/reconciliation_runbook.md` defines the monthly cadence and full reconciliation procedure.
- `seeds/work_ids.txt` does not exist, so seed inventory comparison and seed updates cannot run.
- `data/manifests/coverage_report.json` does not exist, so coverage counts and deltas cannot be reviewed.
- Track 04 must provide an authoritative inventory source, and Track 07 must complete a full bootstrap before monthly reconciliation can produce evidence.
- `nzlc reconcile-work-ids` and `.github/workflows/historical_seed_reconciliation.yml`
  are available for candidate seed comparison before promotion.


## Implementation automation added 2026-06-12

- Added `.github/workflows/monthly_full_reconciliation.yml` for monthly and manual reconciliation.
- The workflow restores the live dataset, validates baseline coverage, discovers or ingests a candidate seed, reconciles it with `seeds/work_ids.txt`, and optionally runs full sync/upload after review.
- See `docs/full_corpus_operations.md` for the operator sequence and review
  artifacts for this workflow.
- Track is `ready` for the first manual reconciliation but remains unable to produce final coverage-delta evidence until Track 07/08 complete.
