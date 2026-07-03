# NZ Gazette Canonical Comparison Builder

Date: 2026-07-03.

Track 46 builds the derived canonical Gazette layer from the four independent
source archives. The canonical layer is reproducible and conflict-aware; it does
not replace the raw source archives.

## Inputs

The builder reads each source archive tree:

- `data/official-gazette`
- `data/digitalnz-gazette`
- `data/victoria-lexisnexis-gazette`
- `data/nzlii-gazette`

Each source tree must contain:

- `records.jsonl`
- `manifests/latest_manifest.json`

Missing source trees are recorded in the comparison report rather than causing
silent omission.

## CLI

```powershell
uv run nzlc nz-gazette-canonical-archive `
  --official-source-dir data/official-gazette `
  --digitalnz-source-dir data/digitalnz-gazette `
  --historical-source-dir data/victoria-lexisnexis-gazette `
  --nzlii-source-dir data/nzlii-gazette `
  --output-dir data/nz-gazette-canonical `
  --year 2026
```

## Outputs

The canonical output tree contains:

- `records.jsonl`
- `canonical_records.jsonl`
- `conflict_queue.jsonl`
- `gazette_conflict_decisions.jsonl`
- `manifests/comparison_report.json`
- `manifests/review_report.json`
- `manifests/coverage_report.json`
- `_state/comparison_state.json`

The archive bundler also writes:

- `dist/corpus-legislation-nz-gazette-canonical-2026.tar.*`
- `dist/corpus-legislation-nz-gazette-canonical-2026.manifest.json`
- `dist/corpus-legislation-nz-gazette-canonical-2026.release-evidence.json`
- `dist/corpus-legislation-nz-gazette-canonical-2026.SHA256SUMS.txt`

## Canonical Rules

- Official Gazette wins by default when it is present.
- DigitalNZ, historical, and NZLII records are supporting sources.
- Exact content agreement raises confidence.
- Conflicts are preserved in `conflict_queue.jsonl` until reviewed decisions are
  supplied.
- Historical-only records remain allowed when the rights caveat is explicit.

## Review Gates

The review report fails closed on:

- missing canonical IDs
- missing supporting sources
- missing provenance
- missing rights notes
- unresolved material conflicts

Missing source trees are recorded as comparison evidence and can be revisited
without mutating the raw source archives.
