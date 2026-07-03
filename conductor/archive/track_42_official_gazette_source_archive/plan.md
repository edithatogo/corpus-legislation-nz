# Plan - Official Gazette Source Archive

## Phase 1 - Discovery And Manifest Contract

- [x] Task: Add official issue discovery tests.
    - [x] Cover issue listing parsing and canonical no-trailing-slash URL use.
    - [x] Cover stable issue IDs and deterministic ordering.
- [x] Task: Define the official source manifest.
    - [x] Include raw artifact paths, HTTP metadata, hashes, timestamps, and
      source URLs.
    - [x] Align fields with the Track 41 raw source schema.
- [x] Task: Conductor - User Manual Verification 'Discovery And Manifest Contract' (Protocol in workflow.md)

## Phase 2 - Retrieval And Extraction

- [x] Task: Implement bounded issue PDF retrieval.
    - [x] Support dry-run, resume state, and conservative request pacing.
    - [x] Store PDFs separately from extracted text.
- [x] Task: Implement bounded notice-page capture.
    - [x] Capture only public pages allowed by the source registry.
    - [x] Store HTML/text extraction with provenance and content hashes.
- [x] Task: Conductor - User Manual Verification 'Retrieval And Extraction' (Protocol in workflow.md)

## Phase 3 - Review And Documentation

- [x] Task: Add source archive review checks.
    - [x] Fail on missing raw artifacts, hashes, provenance, or rights notes.
    - [x] Report extraction failures separately from retrieval failures.
- [x] Task: Document official Gazette archive operation.
    - [x] Include bounded smoke commands and access policy.
    - [x] Explain canonical-preferred status for official source records.
- [x] Task: Conductor - User Manual Verification 'Review And Documentation' (Protocol in workflow.md)

## Validation Evidence

- `uv run pytest -q tests/test_official_gazette_archive.py tests/test_manifest.py tests/test_nz_gazette_source_registry.py tests/test_shared_core_schema.py tests/smoke/test_cli_smoke.py` passed.
- `uv run ruff check src/nz_legislation_corpus/archive.py src/nz_legislation_corpus/cli.py src/nz_legislation_corpus/official_gazette.py tests/test_official_gazette_archive.py` passed.
- `docs/official_gazette_archive.md` documents the official archive CLI and manifest contract.
- `schemas/official_gazette_archive_manifest.schema.json` validates the source-specific manifest.
- `src/nz_legislation_corpus/official_gazette.py` implements URL normalization, issue-link discovery, manifest building, and archive bundling.
- `src/nz_legislation_corpus/archive.py` now supports source-specific archive naming and tar roots.
