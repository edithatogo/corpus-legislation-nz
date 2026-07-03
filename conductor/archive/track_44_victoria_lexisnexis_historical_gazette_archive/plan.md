# Plan - Victoria/LexisNexis Historical Gazette Archive

## Phase 1 - Rights And Access Gate

- [x] Task: Record historical archive rights and access terms.
    - [x] Capture copyright, licence, robots/access, and source ownership
      notes.
    - [x] Define allowed retrieval scope and stop conditions.
- [x] Task: Define historical source identity.
    - [x] Define stable source IDs for year, issue, page, and notice-like
      records where available.
    - [x] Define historical-only caveats for canonical comparison.
- [x] Task: Conductor - User Manual Verification 'Rights And Access Gate' (Protocol in workflow.md)

## Phase 2 - Bounded Historical Archive

- [x] Task: Add historical discovery tests.
    - [x] Cover year index parsing and deterministic ordering.
    - [x] Cover source IDs, page/year references, and rights fields.
- [x] Task: Implement a bounded sample archive.
    - [x] Store raw index/content artifacts separately from normalized output.
    - [x] Write manifests, hashes, and review input files.
- [x] Task: Conductor - User Manual Verification 'Bounded Historical Archive' (Protocol in workflow.md)

## Phase 3 - Review And Canonical Readiness

- [x] Task: Add historical source review checks.
    - [x] Fail on missing rights caveats, source URLs, hashes, or unstable
      source IDs.
    - [x] Report historical-only candidates separately.
- [x] Task: Document historical source use.
    - [x] Explain coverage range, rights caveats, and comparison role.
    - [x] State that bulk retrieval requires the access gate to pass.
- [x] Task: Conductor - User Manual Verification 'Review And Canonical Readiness' (Protocol in workflow.md)

## Validation Evidence

- `uv run pytest tests/test_historical_gazette_archive.py -q` passed.
- `uv run pytest tests/test_official_gazette_archive.py tests/test_digitalnz_gazette_archive.py tests/test_historical_gazette_archive.py -q` passed.
- `uv run ruff check src/nz_legislation_corpus/historical_gazette.py src/nz_legislation_corpus/cli.py tests/test_historical_gazette_archive.py` passed.
- Implementation commit: `7ee077d`
