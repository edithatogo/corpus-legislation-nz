# Contracts

## Environment contract

Required for live sync:

- `NZ_LEGISLATION_API_KEY`
- `HF_TOKEN`
- `HF_REPO_ID`

Required for annual archive:

- `ZENODO_TOKEN`
- `ARCHIVE_CREATORS_JSON`

Required for Zenodo sandbox proof if `ZENODO_TOKEN` is production-scoped:

- `ZENODO_SANDBOX_TOKEN`

Optional:

- `ZENODO_DEPOSITION_ID`
- `ZENODO_API_URL`
- `ARCHIVE_LICENSE`
- `NZLC_SEARCH_TERMS`
- `NZLC_SEARCH_FIELD`
- `NZLC_OUTPUT_DIR`

## CLI contract

- `nzlc doctor`: validate configuration.
- `nzlc sync`: build corpus from official API.
- `nzlc validate`: validate records and write validation report.
- `nzlc manifest`: write manifest and change report.
- `nzlc hf-upload`: upload live corpus to Hugging Face.
- `nzlc archive`: create annual archive and checksums.
- `nzlc zenodo-upload`: create/update Zenodo draft and optionally publish.
- `nzlc smoke-fixture`: generate a local one-record corpus for tests.

## Record contract

Every record must satisfy `schemas/legislation_record.schema.json` and include stable identifiers, source URLs, status/type metadata, extracted text, hashes, and pipeline provenance.

## Artifact contract

Live Hugging Face layout:

```text
data/
  records.jsonl
  parquet/legislation_type=<type>/year=<year>/part-00000.parquet
  raw_xml/<stable_id>.xml
  manifests/latest_manifest.json
  manifests/latest_changes.json
```

Annual archive layout:

```text
dist/archive/
  nz-legislation-corpus-YYYY.tar.zst
  nz-legislation-corpus-YYYY.manifest.json
  nz-legislation-corpus-YYYY.SHA256SUMS.txt
```

## Safety contract

- Do not commit corpus data to GitHub.
- Do not publish Zenodo automatically unless `publish=true` is explicitly passed.
- Do not print secrets.
- Do not delete published Zenodo records.
- Do not claim corpus completeness until discovery coverage is proven.


## Manifest stability contract

`content_sha256` is the canonical no-change comparison value for live uploads. It is based only on stable corpus files: path, size, SHA-256, and record count. It deliberately excludes generated timestamps, manifests, `_state`, cache directories, and bytecode.

`manifest_sha256` is a diagnostic hash for the manifest payload. Do not use local run timestamps to decide whether to upload.

## Coverage contract

`nzlc coverage-report` must be run before public claims about corpus scope. A public release must state whether discovery used:

1. a seed work-id list,
2. API search coverage,
3. an official bulk export, or
4. a reconciliation of the above.
