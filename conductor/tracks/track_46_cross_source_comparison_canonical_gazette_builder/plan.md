# Plan - Cross-Source Comparison And Canonical Gazette Builder

## Phase 1 - Matching And Conflict Policy

- [ ] Task: Define deterministic matching rules.
    - [ ] Cover notice IDs, issue IDs, dates, pages, titles, exact hashes,
      normalized text hashes, and fuzzy text thresholds.
    - [ ] Define unmatched, partial-match, low-confidence, and conflict states.
- [ ] Task: Define canonical precedence and confidence rules.
    - [ ] Apply official, DigitalNZ, Victoria/LexisNexis, NZLII order.
    - [ ] Define how multi-source agreement raises confidence.
- [ ] Task: Conductor - User Manual Verification 'Matching And Conflict Policy' (Protocol in workflow.md)

## Phase 2 - Builder Implementation

- [ ] Task: Add canonical builder tests.
    - [ ] Cover exact matches, metadata-only matches, source conflicts, missing
      source files, and historical-only records.
    - [ ] Cover deterministic reruns and stable canonical IDs.
- [ ] Task: Implement source comparison and canonical output.
    - [ ] Read source manifests without mutating source archives.
    - [ ] Emit canonical records, conflict records, and comparison report.
- [ ] Task: Conductor - User Manual Verification 'Builder Implementation' (Protocol in workflow.md)

## Phase 3 - Review Gates And Documentation

- [ ] Task: Add canonical review gates.
    - [ ] Fail on missing provenance, rights, stable IDs, or unacknowledged
      material conflicts.
    - [ ] Report confidence distribution and source-support counts.
- [ ] Task: Document canonical generation.
    - [ ] Explain derived-output status and reproducibility from source
      manifests.
    - [ ] Explain conflict review and historical-only caveats.
- [ ] Task: Conductor - User Manual Verification 'Review Gates And Documentation' (Protocol in workflow.md)
