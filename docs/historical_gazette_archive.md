# Historical Gazette Archive

Track 44 owns the Victoria/LexisNexis historical New Zealand Gazette source
archive.

## Source Contract

- Source ID: `victoria_lexisnexis_gazette`
- Base URL:
  `https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html`
- Retrieval style: identifiable, conservative, fail-closed
- Canonical eligibility: historical-only evidence unless Track 46 comparison
  work later establishes a reviewable canonical role

## Rights And Access Gate

- Treat this archive as rights-caveated historical evidence.
- Keep the rights note, access note, and source provenance on every record.
- Do not broaden retrieval beyond a bounded sample unless the access gate has
  been reviewed and documented.
- Stealth scraping and access-control bypass are not permitted archive
  mechanisms.

## Supported Inputs

- `records.jsonl`: historical source records with raw index-page evidence and
  extracted issue/page rows
- raw artifact directory: the historical source files that should be bundled
  into the archive

## CLI

```bash
uv run nzlc historical-gazette-export \
  --source-index-url https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html \
  --index-html-path tests/fixtures/victoria_gazette_2008_sample.html \
  --output-dir data/victoria-lexisnexis-gazette \
  --source-year 2008 \
  --max-issue-rows 5

uv run nzlc historical-gazette-archive \
  --records-jsonl data/victoria-lexisnexis-gazette/records.jsonl \
  --source-dir data/victoria-lexisnexis-gazette/raw \
  --output-dir dist/victoria-lexisnexis-gazette \
  --year 2008
```

The export command writes:

- a raw year index capture
- normalized historical source records
- a validation report
- a coverage report
- a source manifest
- an export state file

The archive command writes:

- a source bundle tarball
- a historical source manifest
- a release evidence file
- a SHA256 checksum file

## Manifest Expectations

Each raw historical record must carry:

- stable ID
- source URL
- retrieval method
- retrieval timestamp
- content hash
- rights note
- source-local identifier
- coverage state
- provenance
- year/page references in extraction metadata

## Operational Notes

- Historical records stay separate from official, DigitalNZ, and NZLII raw
  archives.
- The archive is rights-caveated evidence, not canonical truth.
- Issue rows are extracted conservatively from the historical index page and
  should be treated as historical-only candidates until comparison work
  assigns them a canonical role.
