# Plan - Gazette Archive Workflow, Review, And Publication Staging

## Phase 1 - Workflow Contract

- [ ] Task: Define Gazette workflow modes.
    - [ ] Include source-specific bounded smoke harvests and full source
      harvests where permitted.
    - [ ] Include canonical rebuild from existing source manifests.
- [ ] Task: Define artifact layout.
    - [ ] Separate raw source archives, normalized source records, canonical
      records, comparison reports, review reports, manifests, and checksums.
    - [ ] Include blocked-source evidence artifacts.
- [ ] Task: Conductor - User Manual Verification 'Workflow Contract' (Protocol in workflow.md)

## Phase 2 - Workflow Implementation And Tests

- [ ] Task: Add workflow validation tests or static checks.
    - [ ] Cover independent source workflow execution.
    - [ ] Cover canonical rebuild without source re-harvest.
- [ ] Task: Implement staged workflows.
    - [ ] Keep publication disabled by default.
    - [ ] Upload artifacts for review and evidence first.
- [ ] Task: Conductor - User Manual Verification 'Workflow Implementation And Tests' (Protocol in workflow.md)

## Phase 3 - Publication Staging And Documentation

- [ ] Task: Add review and promotion gates.
    - [ ] Fail on missing provenance, rights, hashes, manifests, or
      unacknowledged conflicts.
    - [ ] Require explicit approval before external publication.
- [ ] Task: Document operational use.
    - [ ] Provide manual run commands, artifact review steps, and promotion
      criteria.
    - [ ] Explain that source and canonical archives are separate artifacts.
- [ ] Task: Conductor - User Manual Verification 'Publication Staging And Documentation' (Protocol in workflow.md)
