# Plan - Cross-Source Comparison And Canonical Gazette Builder

## Phase 1 - Matching And Conflict Policy

- [x] Task: Define deterministic matching rules.
    - [x] Cover notice IDs, issue IDs, dates, pages, titles, exact hashes,
      normalized text hashes, and fuzzy text thresholds.
    - [x] Define unmatched, partial-match, low-confidence, and conflict states.
- [x] Task: Define canonical precedence and confidence rules.
    - [x] Apply official, DigitalNZ, Victoria/LexisNexis, NZLII order.
    - [x] Define how multi-source agreement raises confidence.
- [x] Task: Define conflict adjudication artifacts.
    - [x] Specify the queue and reviewed decision file format.
    - [x] Require reviewer, timestamp, rationale, selected value, and evidence
      links for every override.
- [x] Task: Conductor - User Manual Verification 'Matching And Conflict Policy' (Protocol in workflow.md)

## Phase 2 - Builder Implementation

- [x] Task: Add canonical builder tests.
    - [x] Cover exact matches, metadata-only matches, source conflicts, missing
      source files, and historical-only records.
    - [x] Cover deterministic reruns and stable canonical IDs.
- [x] Task: Implement source comparison and canonical output.
    - [x] Read source manifests without mutating source archives.
    - [x] Emit canonical records, conflict records, adjudication queue, and
      comparison report.
- [x] Task: Conductor - User Manual Verification 'Builder Implementation' (Protocol in workflow.md)

## Phase 3 - Review Gates And Documentation

- [x] Task: Add canonical review gates.
    - [x] Fail on missing provenance, rights, stable IDs, or unacknowledged
      material conflicts.
    - [x] Validate reviewed conflict decisions against the queue and source
      evidence.
    - [x] Report confidence distribution and source-support counts.
- [x] Task: Document canonical generation.
    - [x] Explain derived-output status and reproducibility from source
      manifests.
    - [x] Explain conflict review and historical-only caveats.
- [x] Task: Conductor - User Manual Verification 'Review Gates And Documentation' (Protocol in workflow.md)
