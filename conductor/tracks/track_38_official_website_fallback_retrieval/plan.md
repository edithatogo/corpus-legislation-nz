# Plan - Official Website Fallback Retrieval

## Phase 1 - Policy and Fallback Contract

- [ ] Task: Define browser fallback policy.
    - [ ] State allowed and disallowed retrieval behaviours.
    - [ ] Define when browser fallback may run and when it must fail closed.
- [ ] Task: Define fallback provenance and warning contract.
    - [ ] Add fields for retrieval method, source URL, previous failure reason,
      rendered capture hash, and fallback confidence.
    - [ ] Define review-report indicators for browser fallback use.
- [ ] Task: Conductor - User Manual Verification 'Policy and Fallback Contract' (Protocol in workflow.md)

## Phase 2 - Focused Retrieval Tooling

- [ ] Task: Add tests for fallback ordering and provenance.
    - [ ] Cover API/XML/HTML failure followed by official page retrieval.
    - [ ] Cover fail-closed behaviour when browser retrieval is blocked.
- [ ] Task: Implement a small failed-record retry command.
    - [ ] Accept a review report or sync-state failed-version list.
    - [ ] Retry only the requested records with conservative pacing.
- [ ] Task: Integrate Playwright diagnostics where appropriate.
    - [ ] Keep browser setup optional and separate from normal sync.
    - [ ] Capture artifacts for triage without broad crawling.
- [ ] Task: Conductor - User Manual Verification 'Focused Retrieval Tooling' (Protocol in workflow.md)

## Phase 3 - Review and Documentation

- [ ] Task: Extend review output for browser fallback.
    - [ ] Count browser fallback records separately from XML-to-HTML fallback.
    - [ ] Surface unresolved blocked pages for manual triage.
- [ ] Task: Document operational use.
    - [ ] Provide commands, rate-limit guidance, and provenance caveats.
    - [ ] Explain why stealth mode is not part of the standard path.
- [ ] Task: Conductor - User Manual Verification 'Review and Documentation' (Protocol in workflow.md)
