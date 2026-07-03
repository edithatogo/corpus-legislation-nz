# Official Gazette Archive Operation

Track 42 owns the official New Zealand Gazette source archive.

## Source Contract

- Source ID: `official_gazette`
- Base URL: `https://gazette.govt.nz/issues`
- Retrieval style: identifiable, rate-limited, fail-closed
- Canonical eligibility: preferred canonical evidence when public issue pages or PDFs are available

## Supported Inputs

- `records.jsonl`: raw source records for issue PDFs, issue pages, notice pages, and blocked evidence
- raw artifact directory: the source files that should be bundled into the archive

## CLI

```bash
uv run nzlc official-gazette-archive \
  --records-jsonl data/official-gazette/records.jsonl \
  --source-dir data/official-gazette/raw \
  --output-dir dist/official-gazette \
  --year 2026
```

The command writes:

- a source bundle tarball
- a source manifest
- a release evidence file
- a SHA256 checksum file

## Manifest Expectations

Each raw record must carry:

- artifact type
- raw artifact path
- source URL
- retrieval timestamp
- content hash
- rights note
- source-local identifier
- coverage state
- provenance

## Operational Notes

- The archive is source-specific evidence, not canonical truth.
- Official Gazette URLs are normalized to the no-trailing-slash form.
- Issue discovery should use the canonical issue listing and keep public URLs stable.
