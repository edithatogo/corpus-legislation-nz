# Plan - Gazette Source Registry, Rights, And Shared Schema

## Phase 1 - Source Registry And Rights Boundary

- [x] Task: Create the Gazette source registry.
    - [x] Define source IDs, source tiers, base URLs, expected artifacts, and
      canonical eligibility.
    - [x] Record rights, licence, robots/access, and operational caveats for
      each source.
- [x] Task: Define source retrieval limits.
    - [x] Set conservative request pacing and bounded smoke-run rules.
    - [x] State that stealth scraping and access-control bypass are not
      permitted archive mechanisms.
- [x] Task: Define the source coverage matrix.
    - [x] Track coverage by source ID, year, issue ID, notice ID, page range,
      and artifact type.
    - [x] Define gap, overlap, partial-coverage, and blocked-source states.
- [x] Task: Conductor - User Manual Verification 'Source Registry And Rights Boundary' (Protocol in workflow.md)

## Phase 2 - Shared Schemas

- [x] Task: Define the raw source archive schema.
    - [x] Require stable ID, source URL, retrieval method, timestamp, hash,
      artifact path, rights note, and source-local identifiers.
    - [x] Include HTTP metadata where available.
    - [x] Include web-archive-quality capture fields where practical.
- [x] Task: Define the canonical Gazette schema.
    - [x] Require canonical source, supporting sources, conflicts, confidence,
      normalization version, and provenance links.
    - [x] Allow historical-only records only when source-tier and rights caveats
      are explicit.
- [x] Task: Conductor - User Manual Verification 'Shared Schemas' (Protocol in workflow.md)

## Phase 3 - Validation Contract

- [x] Task: Add schema validation tests.
    - [x] Cover complete raw source records and canonical records.
    - [x] Cover missing provenance, missing rights, unstable IDs, and conflict
      fields.
    - [x] Cover coverage-matrix gap and overlap reporting.
- [x] Task: Document the implementation contract for Tracks 42-47.
    - [x] Explain that raw archives remain independent evidence layers.
    - [x] Explain that canonical records are derived and reproducible.
- [x] Task: Conductor - User Manual Verification 'Validation Contract' (Protocol in workflow.md)

## Validation Evidence

- `uv run pytest -q tests/test_nz_gazette_source_registry.py` passed.
- `uv run pytest -q tests/test_shared_core_schema.py` passed.
- `docs/nz_gazette_source_registry.md` documents the source registry,
  canonical precedence, coverage matrix, and downstream track contract.
- `docs/nz_gazette_source_registry.json` validates the registry contract.
- `schemas/nz_gazette_source_registry.schema.json` validates the registry
  structure.
- `schemas/nz_gazette_raw_source_record.schema.json` validates raw archive
  records.
- `schemas/nz_gazette_canonical_record.schema.json` validates canonical
  comparison records.
