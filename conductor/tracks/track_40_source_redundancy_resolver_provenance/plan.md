# Plan - Source Redundancy Resolver and Provenance

## Phase 1 - Resolver Policy and Schema

- [ ] Task: Define source priority and adoption policy.
    - [ ] Specify canonical, fallback-assisted, secondary-corroborated, and
      rescued-source statuses.
    - [ ] Define manual-review gates for non-canonical source promotion.
- [ ] Task: Define retrieval-attempt provenance schema.
    - [ ] Include source name, URL, method, timestamp, status, content hash,
      warning/error text, confidence, and rights note.
    - [ ] Align with shared NZ corpus core provenance fields.
- [ ] Task: Conductor - User Manual Verification 'Resolver Policy and Schema' (Protocol in workflow.md)

## Phase 2 - Integration Points and Review Output

- [ ] Task: Add tests for resolver ordering and reporting.
    - [ ] Cover successful API XML, official HTML fallback, alternate dated URL,
      website fallback, and NZLII candidate states.
    - [ ] Cover deterministic hash/manifest behaviour.
- [ ] Task: Implement resolver state model or adapter contract.
    - [ ] Keep source adapters pluggable and independently testable.
    - [ ] Preserve all failed attempts for auditability.
- [ ] Task: Extend review outputs.
    - [ ] Count records by source status and fallback method.
    - [ ] Emit manual-review queues for secondary-source or low-confidence
      records.
- [ ] Task: Conductor - User Manual Verification 'Integration Points and Review Output' (Protocol in workflow.md)

## Phase 3 - Documentation and Track Coordination

- [ ] Task: Document resolver usage across Tracks 37-39.
    - [ ] Explain how feed signals enqueue API refreshes.
    - [ ] Explain how website and NZLII fallbacks are gated.
- [ ] Task: Update archive and public wording caveats if needed.
    - [ ] Preserve official-source primacy and source-rights warnings.
    - [ ] Avoid public completeness claims until reconciliation evidence exists.
- [ ] Task: Conductor - User Manual Verification 'Documentation and Track Coordination' (Protocol in workflow.md)
