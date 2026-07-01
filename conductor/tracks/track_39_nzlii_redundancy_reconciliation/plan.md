# Plan - NZLII Redundancy Reconciliation

## Phase 1 - Source Inventory and Policy

- [ ] Task: Document NZLII collections, URL patterns, and access caveats.
    - [ ] Identify relevant legislation collection entry points.
    - [ ] Record robots/access/rate-limit considerations.
- [ ] Task: Define NZLII candidate-match schema.
    - [ ] Include source URL, title/date fields, content hash, confidence, and
      match classification.
    - [ ] Keep fallback status separate from canonical source status.
- [ ] Task: Conductor - User Manual Verification 'Source Inventory and Policy' (Protocol in workflow.md)

## Phase 2 - Matching and Reconciliation Reports

- [ ] Task: Add tests for NZLII candidate matching.
    - [ ] Cover exact, probable, ambiguous, and missing classifications.
    - [ ] Cover no-write reconciliation mode.
- [ ] Task: Implement or specify candidate discovery and matching.
    - [ ] Use official metadata as the primary query/matching input.
    - [ ] Preserve all NZLII retrieval and matching provenance.
- [ ] Task: Generate reconciliation reports.
    - [ ] Compare NZLII candidates with seed inventory and bootstrap failures.
    - [ ] Emit manual-review queues for ambiguous candidates.
- [ ] Task: Conductor - User Manual Verification 'Matching and Reconciliation Reports' (Protocol in workflow.md)

## Phase 3 - Optional Text Rescue Path

- [ ] Task: Define guarded text rescue rules.
    - [ ] Require official source failure and explicit fallback marking.
    - [ ] Keep rescued text out of canonical promotion until reviewed.
- [ ] Task: Document operational use and review requirements.
    - [ ] Explain rights/provenance caveats.
    - [ ] Link reconciliation output to Track 07 review evidence.
- [ ] Task: Conductor - User Manual Verification 'Optional Text Rescue Path' (Protocol in workflow.md)
