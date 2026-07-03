# Plan - Gazette Freshness And Change Detection

## Phase 1 - Freshness Source Contract

- [x] Task: Define freshness inputs.
  - [x] Identify official Gazette issue/search/feed surfaces allowed by the
    source registry.
  - [x] Identify DigitalNZ Gazette delta query support through `dnz` or the
    documented API.
- [x] Task: Define freshness state.
  - [x] Include item IDs, source URLs, first/last seen timestamps,
    ETag/Last-Modified where available, content hash where available, and
    enqueue decisions.
  - [x] Include new, changed, unchanged, duplicate, withdrawn/deleted, and
    blocked states.
- [x] Task: Conductor - User Manual Verification 'Freshness Source Contract' (Protocol in workflow.md)

## Phase 2 - Polling And Queue Generation

- [x] Task: Add freshness detection tests.
  - [x] Cover official and DigitalNZ item discovery.
  - [x] Cover deterministic state updates and refresh-queue generation.
- [x] Task: Implement bounded freshness polling.
  - [x] Poll conservatively with source-specific pacing.
  - [x] Store state and emit source refresh queues without broad re-harvests.
- [x] Task: Conductor - User Manual Verification 'Polling And Queue Generation' (Protocol in workflow.md)

## Phase 3 - Workflow And Review Integration

- [x] Task: Integrate freshness queues with archive workflows.
  - [x] Feed targeted refreshes into Tracks 42, 43, 44, and 45 where the
    source is enabled.
  - [x] Trigger Track 46 canonical rebuilds only for affected records or
    bounded windows.
- [x] Task: Document freshness operation.
  - [x] Include manual and scheduled run guidance.
  - [x] Explain how freshness evidence updates the coverage matrix and
    workflow artifacts.
- [x] Task: Conductor - User Manual Verification 'Workflow And Review Integration' (Protocol in workflow.md)

## Evidence

- Workflow: `.github/workflows/nz_gazette_freshness_detection.yml`
- Operator doc: `docs/nz_gazette_freshness_detection.md`
- Freshness layer emits source-specific and combined advisory state, review,
  and queue artifacts.
- Validation: `uv run pytest tests/test_gazette_freshness.py tests/test_nz_gazette_freshness_detection_workflow.py tests/test_official_feed_change_detection_workflow.py tests/test_feed_change.py tests/test_digitalnz_gazette_archive.py tests/test_nz_gazette_canonical.py tests/test_nz_gazette_source_registry.py tests/smoke/test_cli_smoke.py -q`
- Validation: `uv run ruff check src/nz_legislation_corpus/gazette_freshness.py src/nz_legislation_corpus/cli.py tests/test_gazette_freshness.py tests/test_nz_gazette_freshness_detection_workflow.py tests/smoke/test_cli_smoke.py tests/test_nz_gazette_source_registry.py`
- Implementation commit: `4fe4029`
