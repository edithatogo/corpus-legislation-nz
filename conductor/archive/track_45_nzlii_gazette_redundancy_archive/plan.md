# Plan - NZLII Gazette Redundancy Archive

## Phase 1 - Access And Coverage Decision

- [x] Task: Probe NZLII Gazette availability safely.
    - [x] Check robots/access behavior for candidate Gazette URL patterns.
    - [x] Record coverage, rights, and access evidence.
- [x] Task: Define NZLII source-state outcomes.
    - [x] Support usable, partially usable, blocked, and unavailable states.
    - [x] Define revisit criteria for blocked or unavailable states.
- [x] Task: Conductor - User Manual Verification 'Access And Coverage Decision' (Protocol in workflow.md)

## Phase 2 - Source Archive Or Blocked Evidence

- [x] Task: Add tests for NZLII source-state handling.
    - [x] Cover usable sample archive output.
    - [x] Cover blocked/unavailable source evidence.
- [x] Task: Implement the chosen NZLII path.
    - [x] If usable, archive raw artifacts and normalized records separately.
    - [x] If blocked, write source-state evidence and skip harvesting.
- [x] Task: Conductor - User Manual Verification 'Source Archive Or Blocked Evidence' (Protocol in workflow.md)

## Phase 3 - Review And Documentation

- [x] Task: Add NZLII review checks.
    - [x] Fail on missing source-state evidence, rights notes, hashes, or
      provenance.
    - [x] Report NZLII records as secondary-source evidence.
- [x] Task: Document NZLII role.
    - [x] Explain access decision, source status, and comparison use.
    - [x] State that NZLII is not the default canonical source.
- [x] Task: Conductor - User Manual Verification 'Review And Documentation' (Protocol in workflow.md)
