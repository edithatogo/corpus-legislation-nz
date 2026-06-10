# Synthesised and prioritised recommendations

Last reconciled: 2026-06-10.

## Current status

The approved partial/API-discovery launch is complete. GitHub, Hugging Face, and
Zenodo public surfaces exist under the `corpus-legislation-nz` naming line, and
the launch tracking issues are closed. The live dataset remains intentionally
partial and must not be described as complete New Zealand legislation coverage.

Historical publication now uses the separate Hugging Face dataset
`edithatogo/corpus-legislation-nz-historical`. The first historical bootstrap
proved the publication path, but it is not a full historical corpus.

## P0 - Must do before any full-coverage claim

1. Establish corpus discovery completeness: obtain an official work-ID export,
   create a maintained authoritative seed list, or document a reconciliation
   proving API search discovery covers the intended corpus boundary.
2. Turn the historical bootstrap into a stable completeness plan: generate or
   obtain the full historical seed, split it into deterministic resumable
   batches, reconcile candidate seeds with `nzlc reconcile-work-ids`, and
   publish incremental batches only after no-upload review.
3. Keep public wording explicit that the live dataset is partial/API-discovery
   based until Track 04 is closed with evidence.
4. Keep `docs/public_surface_evidence_ledger.md` current before releases,
   DOI updates, repository renames, or full-coverage claims.

## P1 - Strongly recommended

1. Keep Parquet writer options stable.
2. Run daily latest-only sync plus less frequent full reconciliation after the
   seed inventory and maintenance loop are proven.
3. Add alerting via GitHub Actions notifications or a lightweight webhook.
4. Add structural XML extraction after the plain-text corpus is stable.
5. Add a data-quality dashboard from validation reports.
6. Evaluate `zenodraft` for protected draft/version operations before the next
   annual archive cycle.

## P2 - Nice to have

1. Add DuckDB and Polars examples backed by the published Hugging Face dataset.
2. Add a Hugging Face Space for browsing/search.
3. Add OSF mirror only if a concrete preservation or review workflow needs it.
4. Publish generated metadata packages after release review. The generator and
   local validation now exist for Croissant, RO-Crate, Frictionless, DCAT, and
   PROV-O, but generated outputs are not yet public release artifacts.
