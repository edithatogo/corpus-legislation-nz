# Historical corpus bootstrap

The live Hugging Face dataset currently contains an intentionally partial API-discovery corpus. It is not the old or full historical corpus.

Historical bootstrap starts with a deterministic work-ID inventory. Do not run a full historical sync from broad search terms directly, because broad search discovery is not proof of full coverage and is hard to resume or audit.

## Phase 1: discover work IDs

Run a pilot discovery first:

```bash
uv run nzlc discover-work-ids \
  --search-terms "act,bill,regulation,order,notice" \
  --legislation-status historical \
  --legislation-types "act,bill,secondary_legislation,amendment_paper" \
  --max-pages 2 \
  --max-works 50 \
  --output-path generated/historical-work-ids.txt \
  --provenance-path generated/historical-work-ids.provenance.json
```

The GitHub workflow `historical_work_id_discovery.yml` runs the same command and uploads the generated seed/provenance files as an Actions artifact.

## Phase 2: review and promote the seed

Review `historical-work-ids.provenance.json` for:

- search terms and filters used;
- duplicate or empty work IDs;
- unexpected legislation types or statuses;
- whether the result is still only search-derived or has been reconciled against an authoritative inventory.

Only promote a seed file to `seeds/work_ids.txt` when the provenance is acceptable for the intended corpus boundary. If the seed is search-derived only, keep public wording limited to partial/API-discovery coverage.

## Phase 3: historical sync pilot

Use the seed artifact for a small sync pilot:

```bash
NZLC_OUTPUT_DIR=data-historical-pilot uv run nzlc sync \
  --seed-work-ids generated/historical-work-ids.txt \
  --allow-no-search-terms \
  --max-works 50
NZLC_OUTPUT_DIR=data-historical-pilot uv run nzlc validate
NZLC_OUTPUT_DIR=data-historical-pilot uv run nzlc manifest
NZLC_OUTPUT_DIR=data-historical-pilot uv run nzlc coverage-report
```

Do not upload the pilot over the live Hugging Face corpus until the merge policy is explicit. The live corpus currently contains a verified six-record partial corpus.

## Phase 4: full historical bootstrap

After seed review, split the seed file into batches and follow `docs/runtime_capacity_runbook.md`. Preserve `data/_state/sync_state.json` between batches. Upload to Hugging Face only after validation, manifest, and coverage outputs are reviewed.
