# Plan - Gazette Archive Workflow, Review, And Publication Staging

## Phase 1 - Workflow Contract

- [x] Task: Define Gazette workflow modes.
    - [x] Include source-specific bounded smoke harvests and full source
      harvests where permitted.
    - [x] Include canonical rebuild from existing source manifests.
- [x] Task: Define artifact layout.
    - [x] Separate raw source archives, normalized source records, canonical
      records, comparison reports, review reports, manifests, and checksums.
    - [x] Include blocked-source evidence artifacts.
- [x] Task: Define storage, retention, and dedupe policy.
    - [x] Specify compression, content-addressed paths, retained artifact
      classes, expiry rules, and expected size reporting.
    - [x] Include web-archive-quality capture evidence for public web resources
      where practical.
- [x] Task: Conductor - User Manual Verification 'Workflow Contract' (Protocol in workflow.md)

## Phase 2 - Workflow Implementation And Tests

- [x] Task: Add workflow validation tests or static checks.
    - [x] Cover independent source workflow execution.
    - [x] Cover canonical rebuild without source re-harvest.
- [x] Task: Implement staged workflows.
    - [x] Keep publication disabled by default.
    - [x] Upload artifacts for review and evidence first.
    - [x] Emit storage/retention reports with size totals and dedupe rates.
- [x] Task: Conductor - User Manual Verification 'Workflow Implementation And Tests' (Protocol in workflow.md)

## Phase 3 - Publication Staging And Documentation

- [x] Task: Add review and promotion gates.
    - [x] Fail on missing provenance, rights, hashes, manifests, or
      unacknowledged conflicts.
    - [x] Fail on missing storage-retention evidence for large raw artifacts.
    - [x] Require explicit approval before external publication.
- [x] Task: Document operational use.
    - [x] Provide manual run commands, artifact review steps, and promotion
      criteria.
    - [x] Explain that source and canonical archives are separate artifacts.
- [x] Task: Conductor - User Manual Verification 'Publication Staging And Documentation' (Protocol in workflow.md)

## Evidence

- Workflow: `.github/workflows/nz_gazette_archive_staging.yml`
- Operator doc: `docs/nz_gazette_workflow_staging.md`
- Official source archive now emits validation and coverage reports.
- Validation: `uv run pytest tests/test_official_gazette_archive.py tests/test_nz_gazette_workflow_staging.py tests/test_nz_gazette_canonical.py tests/test_nz_gazette_source_registry.py -q`
