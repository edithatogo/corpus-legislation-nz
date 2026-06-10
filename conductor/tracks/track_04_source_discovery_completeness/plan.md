# Plan - Source Discovery Completeness

## Tasks
- [x] Contact or check the NZ Legislation source for an official work ID export or complete inventory.
- [ ] If no official export is available, build `seeds/work_ids.txt` from a documented authoritative inventory.
- [x] Keep comments and provenance in the seed file or adjacent documentation.
- [ ] Reconcile seed coverage against search-based discovery.
- [ ] Define expected counts by legislation type, status, and year where available.
- [x] Document any known exclusions, ephemeral IDs, or incorporated-by-reference caveats.

## Current blocker

- Public NZ Legislation API documentation checked on 2026-06-07 did not identify a complete work-ID export, bulk inventory endpoint, or modified-since enumeration endpoint.
- No authoritative `seeds/work_ids.txt` exists in this repository.
- The remaining tasks require an official export, authoritative inventory, or completed reconciliation source.
- `nzlc reconcile-work-ids` and `.github/workflows/historical_seed_reconciliation.yml`
  now provide a repeatable review step for comparing candidate work-ID
  inventories before promotion.
- `docs/historical_completeness_plan.md` records the staged process for moving
  from bootstrap publication to reviewed completeness.
