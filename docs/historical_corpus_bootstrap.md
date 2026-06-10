# Historical corpus bootstrap

The live Hugging Face dataset currently contains an intentionally partial API-discovery corpus. It is not the old or full historical corpus.

Historical publication uses a separate Hugging Face dataset:
`edithatogo/nz-legislation-corpus-historical`. Do not upload historical records
to `edithatogo/nz-legislation-corpus`.

Historical bootstrap starts with a deterministic work-ID inventory. Do not run a full historical sync from broad search terms directly, because broad search discovery is not proof of full coverage and is hard to resume or audit.

## Phase 1: discover work IDs

Run a pilot discovery first:

```bash
uv run nzlc discover-work-ids \
  --search-terms "act,bill,regulation,order,notice" \
  --legislation-status none \
  --legislation-types "act,bill,secondary_legislation,amendment_paper" \
  --max-pages 2 \
  --max-works 50 \
  --output-path generated/historical-work-ids.txt \
  --provenance-path generated/historical-work-ids.provenance.json
```

The GitHub workflow `historical_work_id_discovery.yml` runs the same command and uploads the generated seed/provenance files as an Actions artifact.

The live API rejected `legislation_status=historical` with HTTP 403 during the
first pilot. Use `none` to omit the status filter while discovering which live
status values and search filters are valid for the historical boundary.

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

The GitHub workflow `historical_sync_pilot.yml` performs this as a no-upload
Actions pilot: it discovers a bounded seed, syncs to `data-historical-pilot`,
validates the records, builds manifests and coverage, records the publication
policy, and uploads those outputs as workflow artifacts only.

Do not upload the pilot over the live Hugging Face corpus. Historical
publication policy is recorded in `docs/historical_publication_policy.md`: the
live Hugging Face dataset remains the verified partial/API-discovery corpus, and
historical outputs stay artifact-only until a separate historical publication
target is explicitly reviewed.

## Phase 4: reviewed bootstrap plan

Track 22 review is recorded in `docs/historical_bootstrap_review.md`.

The reviewed historical publication target is
`edithatogo/nz-legislation-corpus-historical`. Do not upload historical records
to `edithatogo/nz-legislation-corpus`.

The successful pilot artifact from GitHub Actions run `27138352849` produced 52
validated records from 10 search-derived work IDs. It proves the pilot path and
resume state, but not full historical coverage.

The first confirmed historical Hugging Face bootstrap upload completed on
2026-06-09 in GitHub Actions run `27229110053`:

- target: `edithatogo/nz-legislation-corpus-historical`
- upload mode: manual, confirmed
- seed mode: search-derived bootstrap seed, bounded to 500 works
- validation: `ok: true`
- records: 4,550
- raw XML files: 4,550
- Parquet partitions: 83
- years covered: 1908-2026
- source type represented: `act`
- failed versions: 104 reviewed 404 download failures recorded in
  `_state/sync_state.json`
- Hugging Face revision:
  `776ef2737b1e7d629034ef8460d4918e7d979c68`

This upload proves the historical publication path. It is still a bootstrap,
not a complete historical corpus. The remaining project problem is coverage:
identify or generate a stable full work-ID inventory, reconcile it where
possible, then publish in resumable chunks.

After seed review, split the seed file into deterministic batches and follow
`docs/runtime_capacity_runbook.md`. Preserve or restore `records.jsonl`,
`raw_xml/`, `parquet/`, `_state/sync_state.json`, manifests, and coverage
outputs between batches. Upload to Hugging Face only after validation,
manifest, coverage, failed-version state, and the separate historical target
are reviewed.

Use the batch splitter on a reviewed seed file:

```bash
uv run nzlc split-work-id-batches \
  --seed-work-ids seeds/work_ids.txt \
  --output-dir seeds/batches \
  --batch-size 250 \
  --filename-prefix historical-work-ids
```

`seeds/batches/` is ignored by Git by default because operational chunks can be
large and may be regenerated from the reviewed seed. If the full seed becomes a
public coverage contract, commit the reviewed source seed and provenance
explicitly rather than committing ad hoc generated chunks.

For the next historical batch, run `historical_hf_upload.yml` manually with:

- `seed_work_ids_path` set to the reviewed batch file path;
- `restore_existing_historical=true`;
- `replace_existing=false`;
- `upload_confirmed=false` for the review run;
- `upload_confirmed=true` only after reviewing validation, manifest, coverage,
  and failed-version state.

The workflow refuses a confirmed incremental upload when
`restore_existing_historical=false` and `replace_existing=false`. This prevents
an isolated batch from pruning the existing published historical corpus.

Historical upload configuration must use:

```text
HF_HISTORICAL_REPO_ID=edithatogo/nz-legislation-corpus-historical
```

Do not reuse `HF_REPO_ID` for historical publication. The future historical
upload workflow should fail closed unless the historical repository variable is
set and differs from the live partial corpus target.
