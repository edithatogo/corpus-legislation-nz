# Historical bootstrap review

Review date: 2026-06-09

Historical Hugging Face target: `edithatogo/corpus-legislation-nz-historical`

This review covers Track 22 only: historical pilot artifact review and bootstrap
planning. It does not add or approve upload workflow code.

## Artifact evidence

Latest GitHub Actions pilot run checked:
`https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27138352849`

- Workflow: `historical_sync_pilot.yml`
- Event: `workflow_dispatch`
- Status: `success`
- Created: `2026-06-08T12:42:02Z`
- Updated: `2026-06-08T12:43:20Z`
- Head branch: `main`
- Head SHA: `2df717d275d2f853e84ad18089107a625518ed18`
- Artifact name: `historical-sync-pilot`
- Artifact download: the first attempt to `C:/tmp/historical-sync-pilot-27138352849`
  failed with a sandbox filesystem denial; the escalated retry succeeded to
  `C:/tmp/historical-sync-pilot-27138352849`.

The repository also contains a checked-in artifact snapshot under
`generated/historical-sync-pilot-27138352849/`.

## Reviewed files

- `generated/historical-sync-pilot-27138352849/generated/historical-work-ids.provenance.json`
- `generated/historical-sync-pilot-27138352849/data-historical-pilot/manifests/latest_manifest.json`
- `generated/historical-sync-pilot-27138352849/data-historical-pilot/manifests/coverage_report.json`
- `generated/historical-sync-pilot-27138352849/data-historical-pilot/manifests/validation_report.json`
- `generated/historical-sync-pilot-27138352849/data-historical-pilot/_state/sync_state.json`

The older checked-in `generated/historical-pilot/historical-work-ids.provenance.json`
is not the successful pilot seed. It records an empty search-derived inventory
with `record_count: 0`, no work IDs, and 20 queries. Do not promote that empty
provenance file as the bootstrap seed.

## Seed provenance

The successful pilot artifact used a bounded, search-derived seed:

- `record_count`: 10 work IDs
- `generated_at_utc`: `2026-06-08T22:42:19+10:00`
- `legislation_status`: omitted from the query (`null`)
- `legislation_type`: `act`
- `search_field`: `title`
- `search_term`: `act`
- `max_pages`: 1
- `works_added`: 10

Seed work IDs:

```text
act_public_1977_110
act_public_2002_33
act_public_2018_57
act_public_2026_25
act_public_2026_26
act_public_2026_27
act_public_2026_28
act_public_2026_29
act_public_2026_30
act_public_2026_31
```

Caveat: the provenance warning is correct. This is search-derived inventory,
not proof of full historical corpus coverage. Public wording must remain
limited to pilot/bootstrap coverage until the seed is reconciled against an
authoritative inventory.

## Manifest and validation

The pilot produced valid artifact-only output:

- `record_count`: 52
- `manifest_sha256`:
  `3a6e6abdccaa6a8124fece672a708a8f6e61389cd32b575ccc13367a5d23b0ae`
- `content_sha256`:
  `45cc211470f1b02efa9f567ae1689a8ebcdde2dc22c182eccf867efafaee2c31`
- `records.jsonl` SHA-256:
  `60354cf50eb747c77a4e0022a4bc8190f44aab2c7d36263f0751e2f8424d11b0`
- Manifest file count: 57
- Raw XML files: 52
- Parquet files: 4
- Validation: `ok: true`
- Validation errors: none
- Validation warnings: none

Coverage summary:

- `by_type`: `act: 52`
- `by_status`: `in_force: 51`, `not_in_force: 1`
- `by_year`: `1977: 20`, `2002: 20`, `2018: 5`, `2026: 7`
- `ephemeral_identifier_records`: 0
- `missing_text_records`: 0
- `missing_xml_url_records`: 0

## Failed-version and resume state

The sync state supports resume by version hash:

- `works_checked`: 10
- `versions_checked`: 52
- `records_added`: 52
- `records_changed`: 0
- `records_unchanged`: 0
- `records_failed`: 0
- `warnings`: none
- Version hash entries: 52

There is no explicit failed-version queue in the state file because the pilot
had `records_failed: 0`. For future runs, preserve `_state/sync_state.json`
between batches so unchanged versions can be skipped and changed versions can be
detected.

## Bootstrap plan

Use `edithatogo/corpus-legislation-nz-historical` as the historical publication
target. Do not upload historical records to `edithatogo/corpus-legislation-nz`.

Recommended batch progression:

1. Seed audit batch: 50 work IDs, `min_seconds_between_requests=1.0`.
2. First bootstrap batch: 100 work IDs, `min_seconds_between_requests=1.0`.
3. Standard bootstrap batches: 250 work IDs, `min_seconds_between_requests=1.0`.
4. Reduced-risk large batches: only move to 500 work IDs after two consecutive
   250-work batches complete with zero validation errors and no API/rate-limit
   failures.

Resume checkpoints after every batch:

- Preserve `records.jsonl`.
- Preserve `raw_xml/`.
- Preserve `parquet/`.
- Preserve `manifests/latest_manifest.json`.
- Preserve `manifests/coverage_report.json`.
- Preserve `_state/sync_state.json`.
- Record workflow run URL, seed slice, record count, manifest hash, content
  hash, validation result, coverage summary, and failed-version summary.

Stop conditions:

- Any validation error.
- Any missing-text or missing-XML risk indicator above zero.
- Any unexpected ephemeral identifier records.
- Any non-zero failed-version count, unless the failed versions are reviewed
  and explicitly added to a retry/waiver log.
- API 403/401 authentication or permission failures.
- Sustained API 429/rate-limit failures after lowering pacing.
- A manifest hash or content hash mismatch between local artifact and intended
  upload source.
- Evidence that the seed is broader or narrower than the documented historical
  boundary.

Publication gate:

- Track 21 must create or document the separate historical dataset shell.
- Track 23 must remain manual-only and disabled until the seed boundary,
  reviewed batch outputs, and upload target are explicit.
- The first historical Hugging Face upload must be a reviewed manual run to
  `edithatogo/corpus-legislation-nz-historical`, not a scheduled workflow.
