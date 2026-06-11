# Historical corpus completeness plan

Last updated: 2026-06-11.

This plan moves the historical dataset from a successful 500-work bootstrap to a
reviewed completeness process. It does not claim that historical coverage is
complete today.

## Current state

- Live dataset: `edithatogo/corpus-legislation-nz`.
- Historical dataset: `edithatogo/corpus-legislation-nz-historical`.
- Historical bootstrap publication path works.
- Current historical dataset is a bootstrap, not a complete historical corpus.
- Broad no-limit API discovery completed in GitHub Actions run `27313765016`
  and produced a search-derived candidate inventory with 33,693 unique work IDs.
- No authoritative `seeds/work_ids.txt` is present.
- Full coverage remains blocked until a complete work-ID inventory is obtained
  or a documented reconciliation proves that discovery covers the intended
  boundary.

## Completeness boundary

The historical completeness target is a reviewed work-ID inventory for the
intended New Zealand legislation boundary, with provenance sufficient to explain:

- source of the inventory;
- search terms, type filters, status filters, and pagination limits, if
  search-derived;
- whether an official export or independent source was used;
- known exclusions;
- duplicate and removed work IDs between candidate inventories;
- batch hashes for resumable upload;
- failed-version state after each sync batch.

Search-derived discovery alone remains a candidate inventory, not proof of
complete coverage.

## Stage 1 - Generate a candidate inventory

Preferred input is an official or maintained full work-ID export. If unavailable,
generate a candidate from broad API discovery and preserve its provenance:

```bash
uv run nzlc discover-work-ids \
  --search-terms "act,bill,regulation,order,notice" \
  --legislation-status none \
  --legislation-types "act,bill,secondary_legislation,amendment_paper" \
  --output-path generated/historical-work-ids.candidate.txt \
  --provenance-path generated/historical-work-ids.candidate.provenance.json
```

For pilots, keep `--max-pages` and `--max-works`. For a completeness candidate,
remove those limits only on a controlled runner and preserve the provenance
artifact.

The manual GitHub Actions workflow `historical_work_id_discovery.yml` keeps
pilot-safe defaults of `max_pages=2` and `max_works=50`. For a no-limit
candidate discovery run, dispatch that workflow with `max_pages=none` and
`max_works=none`; blank inputs may be replaced by GitHub's workflow defaults.

Current candidate evidence:

- GitHub Actions run: `27313765016`.
- Artifact: `historical-work-id-discovery`.
- Local artifact path after download:
  `generated/historical-discovery-27313765016/`.
- Search terms: `act,bill,regulation,order,notice`.
- Legislation types: `act,bill,secondary_legislation,amendment_paper`.
- Legislation status filter: omitted via `none`.
- Candidate unique work IDs: 33,693.
- Candidate SHA-256:
  `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`.
- Provenance warning: search-derived inventory only; not authoritative
  completeness proof.

## Stage 2 - Reconcile before promotion

Compare the candidate against the current reviewed baseline before promoting or
batching it:

```bash
uv run nzlc reconcile-work-ids \
  --baseline-work-ids seeds/work_ids.txt \
  --candidate-work-ids generated/historical-work-ids.candidate.txt \
  --report-path generated/historical-work-id-reconciliation.json \
  --merged-output-path generated/historical-work-ids.merged.txt \
  --baseline-label reviewed-baseline \
  --candidate-label expanded-discovery
```

The same operation is available through the manual GitHub Actions workflow
`historical_seed_reconciliation.yml`. The workflow uploads the reconciliation
report and optional merged seed as an artifact. It does not sync records and
does not upload to Hugging Face.

Review before promotion:

- `added_count` and `added_work_ids`;
- `removed_count` and `removed_work_ids`;
- `baseline_sha256`, `candidate_sha256`, and `merged_sha256`;
- provenance for the candidate source;
- whether removed work IDs are real removals, filter drift, or discovery gaps.

Only commit or promote a merged seed after this review. If the seed is still
search-derived, public wording must continue to say coverage is not proven
complete.

Current reconciliation evidence:

- Baseline:
  `generated/historical-sync-pilot-27138352849/generated/historical-work-ids.txt`
  from the reviewed historical sync pilot.
- Baseline unique work IDs: 10.
- Baseline SHA-256:
  `828ee48a61c858c8aac5bb4bd0c0f37c05a307e11d81c5dcfe7f3c3a65b9fad1`.
- Candidate unique work IDs: 33,693.
- Added work IDs: 33,683.
- Removed work IDs: 0.
- Reconciliation report:
  `generated/historical-discovery-27313765016/historical-work-id-reconciliation-vs-10-work-pilot.json`.
- The candidate contains the pilot seed but remains search-derived and should
  not be promoted as authoritative full coverage without external review.

## Stage 3 - Split reviewed batches

After review, split the promoted seed into deterministic batches:

```bash
uv run nzlc split-work-id-batches \
  --seed-work-ids seeds/work_ids.txt \
  --output-dir seeds/batches \
  --batch-size 250 \
  --filename-prefix historical-work-ids
```

Keep the batch manifest with the review artifact. It records the seed hash,
batch hashes, first/last work IDs, and batch counts. Operational batch files are
ignored by Git by default unless a future track explicitly chooses to commit
reviewed public seed chunks.

Current batch plan:

- Batch size: 500 work IDs.
- Batch count: 68.
- First reviewed workflow seed:
  `seeds/reviewed/historical-work-ids-0001.txt`.
- Batch manifest:
  `generated/historical-discovery-27313765016/historical-work-id-batches.manifest.json`.
- Batch directory:
  `generated/historical-discovery-27313765016/batches/`.
- Seed SHA-256:
  `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`.

## Stage 4 - No-upload validation

Run `historical_hf_upload.yml` manually with:

- `seed_work_ids_path` set to the reviewed batch file path;
- `merge_policy=restore_merge`;
- `max_works=none` so the workflow does not apply the pilot default limit;
- `upload_confirmed=false`.

Review the artifact:

- validation report;
- manifest and manifest hash;
- coverage report;
- `_state/sync_state.json`;
- failed-version warnings;
- record counts by type, status, and year.

Current no-upload batch evidence:

- GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27316467370`.
- Result: success.
- Upload behavior: `upload_confirmed=false`; the Hugging Face upload step was
  skipped.
- Reviewed seed path: `seeds/reviewed/historical-work-ids-0001.txt`.
- Reviewed seed work IDs: 500.
- Reviewed seed SHA-256:
  `59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
- Restored/merged output record count: 4,737.
- Validation report: `ok=true`; record count 4,737.
- Coverage report: 4,737 `act` records; 4,466 `in_force`, 271
  `not_in_force`; 0 ephemeral identifiers, 0 missing text records, and 0
  missing XML URL records.
- Latest manifest SHA-256:
  `19e5f5c8eb25307d170105659d20d459a42fea8668eb424223abc40b844bea51`.
- Sync state: 623 versions checked, 187 records added, 436 records failed, and
  118 Parquet files written.
- Failed-version pattern: 404 responses for early local/imperial Act XML URLs,
  including `act_local_1841_1` through `act_local_1889_22` examples in the
  first reviewed batch.

Decision after triage: XML 404s for early local/imperial Acts are remediated by
falling back to the equivalent HTML format when the API advertises both formats.
No-upload rerun `27330484544` passed with 5,173 records, 0 failed records, and
436 XML-to-HTML fallback warnings.

## Stage 5 - Confirmed incremental upload

Only after no-upload review, rerun the same batch with:

- `merge_policy=restore_merge`;
- `max_works=none`;
- `upload_confirmed=true`.

Do not use `merge_policy=no_restore_incremental` for a confirmed incremental
upload. A fresh runner without restore has no previous records and could prune
published historical files.

Batch 0001 is no longer blocked by failed-version state. The 436 XML failures
from no-upload run `27316467370` were remediated by XML-to-HTML fallback in
rerun `27330484544` and confirmed upload run `27331999831`.

Confirmed batch 0001 evidence:

- GitHub Actions run:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27331999831`.
- Result: success.
- Upload behavior: `upload_confirmed=true`; historical Hugging Face upload step
  completed.
- Historical Hugging Face dataset:
  `edithatogo/corpus-legislation-nz-historical`.
- Verified Hugging Face revision after upload:
  `dcc92964ef832c7e0bd2f904f88de523998304f2`.
- Reviewed seed path: `seeds/reviewed/historical-work-ids-0001.txt`.
- Reviewed seed work IDs: 500.
- Reviewed seed SHA-256:
  `59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
- Restored/merged output record count: 5,173.
- Validation report: `ok=true`; record count 5,173.
- Coverage report: 5,173 `act` records; 4,550 `in_force`, 623
  `not_in_force`; 0 ephemeral identifiers, 0 missing text records, and 0
  missing XML URL records.
- Latest manifest SHA-256:
  `1c970def5f65971bb6f5e7403a0bc731a52d422c8d47773b9fa5df6f220569a5`.
- Sync state: 623 versions checked, 623 records added, 0 records failed, and
  128 Parquet files written.
- Warnings: 436 XML-to-HTML fallback warnings for early local/imperial Act XML
  404s. These are not failed versions because equivalent HTML content was
  fetched and preserved.

## Stage 6 - Completeness declaration

Historical completeness can be declared only after:

- the seed source is authoritative or reconciled;
- all reviewed batches have run;
- failed versions are triaged;
- coverage report and manifest are reviewed;
- Hugging Face historical revision is recorded;
- public README/dataset-card wording is updated without overstating source
  rights or completeness.

Until then, the correct public statement is: historical publication is a
bootstrap with reviewed publication mechanics, not a proven complete historical
corpus.
