# Spec - Monthly Full Reconciliation

## Status
ready

## Goal
keep the corpus complete over time, not only during the first bootstrap.

## Acceptance Criteria
- Reconciliation cadence is documented.
- Seed changes are reviewed.
- Coverage deltas are explained in `latest_changes.json` or a maintenance note.

## Evidence to Record
- Reconciliation date.
- Added or removed work IDs.
- Coverage deltas.

## Evidence Recorded

- Reconciliation cadence documented on 2026-06-07:
  - `docs/reconciliation_runbook.md` defines monthly reconciliation after first full bootstrap.
  - The runbook allows quarterly reconciliation only after a recorded maintainer decision.
  - `docs/maintenance_runbook.md` now points monthly maintenance to the full reconciliation procedure.
- Local inventory/output check on 2026-06-07:
  - `seeds/work_ids.txt`: absent.
  - `data/manifests/coverage_report.json`: absent.
- Current reconciliation result:
  - No reconciliation run was performed.
  - Added work IDs: none.
  - Removed work IDs: none.
  - Coverage deltas: unavailable because no full corpus coverage report exists.

## Blocked Items

- Cannot compare seed inventory, search discovery, and coverage output until an authoritative `seeds/work_ids.txt` and full corpus coverage report exist.
- Cannot add newly discovered work IDs with provenance until Track 04 produces or identifies an authoritative inventory source.
- Cannot rerun full sync in staged batches until Track 07 is unblocked.
- Cannot explain coverage deltas in `latest_changes.json` or a maintenance note until a real full reconciliation run has outputs to compare.
