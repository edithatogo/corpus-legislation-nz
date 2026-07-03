# Plan - DigitalNZ Gazette Source Archive

Implementation commit: `e37a032`

## Phase 1 - dnz Integration Contract

- [x] Task: Validate the local `dnz` CLI path and capabilities.
    - [x] Confirm `dnz search` can express `primary_collection=New Zealand
      Gazette`.
    - [x] Decide whether anonymous public API support or `DIGITALNZ_API_KEY`
      is required for regular harvesting.
      - Decision: require `DIGITALNZ_API_KEY` for live export runs and track
        the reusable exporter gap in `edithatogo/dnz` issue #1.
- [x] Task: Create or link the `dnz` dependency track.
    - [x] Track Gazette export mode, deterministic paging, JSONL/page
      manifests, and validation evidence in the `dnz` repo.
    - [x] Record the `dnz` issue, PR, or track link in this track before
      relying on cross-repo behavior.
- [x] Task: Define the DigitalNZ source manifest.
    - [x] Include query parameters, page state, API metadata, timestamps,
      hashes, and output paths.
    - [x] Align fields with the Track 41 raw source schema.
- [x] Task: Conductor - User Manual Verification 'dnz Integration Contract' (Protocol in workflow.md)

## Phase 2 - Resumable Export

- [x] Task: Add tests for DigitalNZ Gazette export planning.
    - [x] Cover stable query parameters and deterministic page ordering.
    - [x] Cover resume state and per-page manifest entries.
- [x] Task: Implement or wire a bounded export wrapper.
    - [x] Reuse `dnz` for API calls where practical.
    - [x] Store raw API pages separately from normalized JSONL records.
- [x] Task: Conductor - User Manual Verification 'Resumable Export' (Protocol in workflow.md)

## Phase 3 - Review And Comparison Readiness

- [x] Task: Add DigitalNZ source review checks.
    - [x] Fail on missing rights fields, source URLs, landing URLs, IDs, or
      manifest hashes.
    - [x] Report metadata-only records separately from text-bearing records.
- [x] Task: Document DigitalNZ archive use.
    - [x] Explain `dnz` dependency, credential handling, and source status.
    - [x] Explain how DigitalNZ corroborates official and historical sources.
- [x] Task: Conductor - User Manual Verification 'Review And Comparison Readiness' (Protocol in workflow.md)
