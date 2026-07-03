# NZ Gazette Workflow Staging

Track 47 stages the Gazette source archives and the derived canonical Gazette
layer without promoting either layer to a public publication surface.

The staging workflow lives at:

- `.github/workflows/nz_gazette_archive_staging.yml`

## What It Stages

- Official Gazette source archives from `data/official-gazette/`.
- DigitalNZ Gazette source archives from `data/digitalnz-gazette/`.
- Victoria/LexisNexis historical Gazette archives from
  `data/victoria-lexisnexis-gazette/`.
- NZLII Gazette redundancy archives from `data/nzlii-gazette/`.
- The derived canonical Gazette layer from the four independent source
  archives.

## Inputs

- `stage_mode`: `source`, `canonical`, or `full`.
- `source_scope`: `all` or one source ID.
- `year`: archive year used for bundled tarball names.
- `comparison_run_id`: comparison provenance recorded in the canonical report.
- `decisions_path`: optional canonical conflict-decision JSONL.
- `minimum_free_gb`: disk gate for the staging runner.
- `publish_confirmed`: must remain `false`.

## Artifact Contract

The workflow uploads a single artifact bundle named
`nz-gazette-archive-staging` that contains:

- raw source archives and manifests for each staged source
- canonical comparison, review, and coverage reports
- checksums and release evidence
- a staging report that records artifact sizes, dedupe counts, and publication blocking state

## Promotion Rules

- Raw source archives remain immutable evidence layers.
- Canonical records remain derived and reproducible from source manifests.
- External publication is disabled in this workflow.
- Any later publication step must use the downstream protected publication
  track after manual review.

## Usage

Example manual staging run:

```bash
gh workflow run "NZ Gazette archive staging" \
  --field stage_mode=full \
  --field source_scope=all \
  --field year=2026 \
  --field comparison_run_id=gazette-compare-manual
```

The checked-in source layers should already exist locally or have been restored
before the workflow is dispatched.
