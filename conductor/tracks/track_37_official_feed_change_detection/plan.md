# Plan - Official Feed Change Detection

## Phase 1 - Source Discovery and Contract

- [ ] Task: Document official feed/API update sources and caveats.
    - [ ] Capture feed URL patterns, API/search parameters, and timestamp fields.
    - [ ] Record rights, rate-limit, and completeness caveats.
- [ ] Task: Define feed-state and refresh-queue schemas.
    - [ ] Specify feed item identity, source URL, timestamps, content hash, and
      mapping status fields.
    - [ ] Specify refresh queue fields for work IDs, version IDs, and unmapped
      review candidates.
- [ ] Task: Conductor - User Manual Verification 'Source Discovery and Contract' (Protocol in workflow.md)

## Phase 2 - Polling and Mapping

- [ ] Task: Add tests for feed polling and mapping behaviour.
    - [ ] Cover duplicate feed entries and repeated polling.
    - [ ] Cover mapped work/version IDs and unmapped candidate reporting.
- [ ] Task: Implement feed polling and state persistence.
    - [ ] Use structured XML/feed parsing instead of ad hoc text matching.
    - [ ] Preserve retrieval provenance and source hashes.
- [ ] Task: Implement refresh queue generation.
    - [ ] Enqueue canonical API refreshes for mapped items.
    - [ ] Emit review candidates for unmapped items.
- [ ] Task: Conductor - User Manual Verification 'Polling and Mapping' (Protocol in workflow.md)

## Phase 3 - Workflow Integration and Evidence

- [ ] Task: Add a conservative scheduled/manual workflow entry point.
    - [ ] Keep it advisory and separate from full bootstrap writes.
    - [ ] Upload feed-state and refresh-queue artifacts.
- [ ] Task: Update documentation and Track 07 handoff notes.
    - [ ] Explain how feed signals complement the full archive scheduler.
    - [ ] Record validation commands and example artifact paths.
- [ ] Task: Conductor - User Manual Verification 'Workflow Integration and Evidence' (Protocol in workflow.md)
