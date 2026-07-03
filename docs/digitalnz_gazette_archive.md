# DigitalNZ Gazette Archive

Track 43 archives the DigitalNZ New Zealand Gazette source layer as a separate
evidence stream. The corpus repo now provides a bounded export wrapper plus an
archive bundler.

## Dependency Note

- Reusable exporter gap tracked in `edithatogo/dnz` issue #1:
  <https://github.com/edithatogo/dnz/issues/1>
- The local corpus wrapper uses the DigitalNZ API directly for the archive
  smoke path and records the `dnz` dependency boundary in the export manifest.
- Live exports require `DIGITALNZ_API_KEY`. Anonymous export is not the chosen
  compatibility mode for this track.

## Export Layout

The export command writes a source tree like:

- `data/digitalnz-gazette/source_records.jsonl`
- `data/digitalnz-gazette/records.jsonl`
- `data/digitalnz-gazette/raw/pages/page-0001.json`
- `data/digitalnz-gazette/raw/items/<stable-id>.json`
- `data/digitalnz-gazette/manifests/latest_manifest.json`
- `data/digitalnz-gazette/manifests/validation_report.json`
- `data/digitalnz-gazette/manifests/coverage_report.json`
- `data/digitalnz-gazette/_state/export_state.json`
- `data/digitalnz-gazette/_state/page_index.jsonl`

## Commands

```powershell
uv run nzlc digitalnz-gazette-export `
  --output-dir data/digitalnz-gazette `
  --api-key $env:DIGITALNZ_API_KEY `
  --query-text Gazette `
  --collection-filter "New Zealand Gazette" `
  --page-size 100 `
  --max-pages 1
```

```powershell
uv run nzlc digitalnz-gazette-archive `
  --source-dir data/digitalnz-gazette `
  --output-dir dist/digitalnz-gazette `
  --year 2026
```

## Review Gates

The export review fails on:

- missing rights metadata
- missing source URLs or landing URLs
- missing record IDs
- missing manifest hashes

Metadata-only records are allowed, but they are reported separately from
text-bearing DigitalNZ records. The archive bundle remains corroborative source
evidence and never replaces the official Gazette or the canonical comparison
layer.

