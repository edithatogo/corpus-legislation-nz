# Plan - Official Feed Change Detection

## Phase 1 - Source Discovery and Contract

- [x] Task: Document official feed/API update sources and caveats.
    - [x] Capture feed URL patterns, API/search parameters, and timestamp fields.
    - [x] Record rights, rate-limit, and completeness caveats.
- [x] Task: Define feed-state and refresh-queue schemas.
    - [x] Specify feed item identity, source URL, timestamps, content hash, and
      mapping status fields.
    - [x] Specify refresh queue fields for work IDs, version IDs, and unmapped
      review candidates.
- [ ] Task: Conductor - User Manual Verification 'Source Discovery and Contract' (Protocol in workflow.md)

## Phase 2 - Polling and Mapping

- [x] Task: Add tests for feed polling and mapping behaviour.
    - [x] Cover duplicate feed entries and repeated polling.
    - [x] Cover mapped work/version IDs and unmapped candidate reporting.
- [x] Task: Implement feed polling and state persistence.
    - [x] Use structured XML/feed parsing instead of ad hoc text matching.
    - [x] Preserve retrieval provenance and source hashes.
- [x] Task: Implement refresh queue generation.
    - [x] Enqueue canonical API refreshes for mapped items.
    - [x] Emit review candidates for unmapped items.
- [ ] Task: Conductor - User Manual Verification 'Polling and Mapping' (Protocol in workflow.md)

## Phase 3 - Workflow Integration and Evidence

- [ ] Task: Add a conservative scheduled/manual workflow entry point.
    - [x] Keep it advisory and separate from full bootstrap writes.
    - [ ] Upload feed-state and refresh-queue artifacts.
- [x] Task: Update documentation and Track 07 handoff notes.
    - [x] Explain how feed signals complement the full archive scheduler.
    - [x] Record validation commands and example artifact paths.
- [ ] Task: Conductor - User Manual Verification 'Workflow Integration and Evidence' (Protocol in workflow.md)
