# Historical corpus publication policy

The live Hugging Face dataset `edithatogo/nz-legislation-corpus` remains the
verified partial/API-discovery corpus. Historical corpus outputs must not be
uploaded over that dataset.

## Policy

Historical corpus builds are staged separately until a reviewed full seed and
publication workflow are ready.

- Keep `edithatogo/nz-legislation-corpus` for the current verified partial
  corpus line.
- Treat `historical_sync_pilot.yml` outputs as artifact-only publication
  candidates.
- Do not publish historical records to Hugging Face from the pilot workflow.
- If historical outputs are published later, use a separate dataset repository
  such as `edithatogo/nz-legislation-corpus-historical`, or another explicitly
  documented historical target.
- Keep public wording explicit that search-derived historical seeds are partial
  until reconciled against an authoritative inventory.

## Required proof before historical publication

Before any historical upload workflow is added or enabled:

- run a bounded artifact-only pilot from `historical_sync_pilot.yml`;
- review `generated/historical-work-ids.provenance.json`;
- review `data-historical-pilot/manifests/latest_manifest.json`;
- review `data-historical-pilot/manifests/coverage_report.json`;
- confirm failed-version state in `data-historical-pilot/_state/sync_state.json`;
- record the intended Hugging Face target dataset and whether it is separate
  from the current live partial corpus.

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
