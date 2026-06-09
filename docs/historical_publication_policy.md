# Historical corpus publication policy

The live Hugging Face dataset `edithatogo/nz-legislation-corpus` remains the
verified partial/API-discovery corpus. Historical corpus outputs must not be
uploaded over that dataset.

## Policy

Historical corpus builds are staged separately until a reviewed full seed and
publication workflow are ready.

- Keep `edithatogo/nz-legislation-corpus` for the current verified partial
  corpus line.
- Use `edithatogo/nz-legislation-corpus-historical` as the historical corpus
  publication target.
- Treat `historical_sync_pilot.yml` outputs as artifact-only publication
  candidates.
- Do not publish historical records to Hugging Face from the pilot workflow.
- If historical outputs are published later, publish them only to
  `edithatogo/nz-legislation-corpus-historical`, unless a later reviewed change
  records a replacement historical target.
- Configure GitHub historical upload workflows with `HF_HISTORICAL_REPO_ID`.
  They must not fall back to `HF_REPO_ID`.
- Keep historical upload workflows manual-only. Do not add a `schedule` trigger
  unless a later reviewed track deliberately approves maintenance automation.
- Make the first workflow proof a dry-run/no-upload run. Real historical writes
  require an explicit manual upload choice after target and batch-plan review.
- Keep public wording explicit that search-derived historical seeds are partial
  until reconciled against an authoritative inventory.

## Required proof before historical publication

Before any real historical upload run is enabled or performed:

- run a bounded artifact-only pilot from `historical_sync_pilot.yml`;
- review `generated/historical-work-ids.provenance.json`;
- review `data-historical-pilot/manifests/latest_manifest.json`;
- review `data-historical-pilot/manifests/coverage_report.json`;
- confirm failed-version state in `data-historical-pilot/_state/sync_state.json`;
- confirm `HF_HISTORICAL_REPO_ID` is set to
  `edithatogo/nz-legislation-corpus-historical`;
- confirm `HF_HISTORICAL_REPO_ID` is not equal to `HF_REPO_ID`;
- confirm the planned workflow has no scheduled trigger and fails before upload
  when `HF_HISTORICAL_REPO_ID` is absent or equal to `HF_REPO_ID`.

## Historical upload guardrails

The historical upload path is fail-closed:

- If `HF_HISTORICAL_REPO_ID` is absent, stop before any data sync or upload.
- If `HF_HISTORICAL_REPO_ID` equals `HF_REPO_ID`, stop before any data sync or
  upload.
- If the manual run is not explicitly approved for upload, run validation,
  manifest, and coverage generation only.
- Do not write to `edithatogo/nz-legislation-corpus` from historical workflows.

This keeps the live partial/API-discovery dataset protected by default while
allowing a reviewed historical dataset to be staged separately.

## Current pilot evidence

The first no-upload pilot ran in GitHub Actions run `27138352849`.

- Inputs: `legislation_status=none`, `max_pages=1`, `max_works=10`,
  `min_seconds_between_requests=0.5`.
- Seed work IDs: 10.
- Validated output records: 52.
- Manifest SHA-256:
  `3a6e6abdccaa6a8124fece672a708a8f6e61389cd32b575ccc13367a5d23b0ae`.
- Content SHA-256:
  `45cc211470f1b02efa9f567ae1689a8ebcdde2dc22c182eccf867efafaee2c31`.

This evidence proves the pilot path, not full historical coverage.
