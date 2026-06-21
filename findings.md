# Findings & Scratchpad

## LIBRARIAN RESEARCH — Full Corpus Bootstrap Download

### Research completed: 2026-06-14

---

## 1. Codebase Architecture Overview

### Source package: `src/nz_legislation_corpus/`

| Module | Purpose |
|--------|---------|
| `cli.py` | Typer-based CLI (`nzlc` command), all subcommands: sync, validate, manifest, hf-upload, discover-work-ids, split-work-id-batches, reconcile-work-ids, coverage-report, archive, zenodo-upload, doctor, smoke-fixture, metadata-packages, rss-feed |
| `nz_api.py` | `NZLegislationClient` — HTTP client for official NZ Legislation API (`api.legislation.govt.nz/v0`). X-Api-Key auth, 429/403/5xx retry with exponential backoff, rate-limit low-quota sleeping, configurable pacing (`min_seconds_between_requests`) |
| `schema.py` | Constants: `RECORD_SCHEMA_VERSION = "1.0"`, `RECORD_SCHEMA_ID = "nzlc-record-v1"` |
| `normalize.py` | `normalize_version_record()` — transforms raw API version dict + raw content into normalized record dict with all required fields |
| `validate.py` | `validate_records()` — JSON Schema (Draft202012) validation + required-field checks + SHA-256 text hash verification + duplicate detection |
| `config.py` | `Settings` class (Pydantic Settings) reading from environment variables with aliases |
| `discovery.py` | Work-ID inventory building, batch splitting, reconciliation between seed inventories |
| `manifest.py` | `build_manifest()` and `build_change_report()` for data directory content hashing |
| `hf_sync.py` | Hugging Face upload (via `hf upload-large-folder` with fallback to `HfApi.upload_folder`) and stale file pruning |
| `types.py` | `SyncStats` dataclass and `FormatLink` |
| `archive.py` | Yearly archive builder |
| `zenodo.py` | Zenodo draft upload and publish |
| `extract_text.py` | Text extraction from XML/HTML |
| `parquet_writer.py` | Partitioned Parquet writer |
| `rss_feed.py` | RSS feed generator |
| `metadata_packages.py` | Croissant, RO-Crate, Frictionless, DCAT, PROV-O generation |
| `embeddings.py` | BGE-M3 embeddings (optional) |
| `utils.py` | File I/O, hashing helpers |
| `artifact_provenance.py` | Attestation artifact creation |
| `osf_optional.py` | OSF integration (optional) |

### Key dependency versions (from pyproject.toml):
- Python >= 3.11
- requests, click, typer, rich, pyarrow, polars, defusedxml, huggingface_hub, hf-xet, jsonschema, zstandard, pydantic, pydantic-settings

---

## 2. Schema Landscape

### Legislation Record Schema (`schemas/legislation_record.schema.json`)
- JSON Schema Draft 2020-12
- `$id`: `https://example.org/schemas/nz-legislation-record.schema.json`
- 26 **required** fields: `stable_id`, `record_schema_version` (const: "1.0"), `work_id`, `version_id`, `title`, `jurisdiction` (const: "New Zealand"), `country` (const: "NZ"), `source`, `source_url`, `api_url`, `legislation_type`, `legislation_status`, `scrape_date`, `ingest_timestamp_utc`, `language`, `text`, `text_sha256` (pattern: `^[a-f0-9]{64}$`), `source_hash` (pattern: `^[a-f0-9]{64}$`), `pipeline_version`
- Optional fields: `xml_url`, `html_url`, `pdf_url`, `legislation_subtype`, `version_date`, `year`, `administering_agencies`, `is_latest_version`, `raw_xml_sha256`, `raw_content_sha256`, `id_is_ephemeral`, `id_ephemeral_reason`, `raw_version_metadata`
- `additionalProperties: true`

### Shared NZ Corpus Core Schema (`schemas/shared_nz_corpus_core.schema.json`)
- Cross-corpus compatibility between legislation and Hansard
- Required: `corpus_id` (enum: "corpus-nz-legislation" | "corpus-nz-hansard"), `record_id`, `source_id`, `jurisdiction`, `country`, `document_type`, `display_title`, `language`, `record_schema_version`, `canonical_uri`, `source_url`, `source_version`, `effective_date`, `published_date`, `last_modified_date`, `content_sha256`, `manifest_sha256`, `coverage_status`, `rights_note`, `provenance`

### Release Evidence Schema (`schemas/release_evidence.schema.json`)
- Used for Zenodo archive release evidence files

---

## 3. Full Corpus Bootstrap Workflow (`full_corpus_bootstrap.yml`)

### Trigger: `workflow_dispatch` (manual only)

### Inputs:
| Input | Default | Purpose |
|-------|---------|---------|
| `seed_work_ids_path` | `seeds/work_ids.txt` | Reviewed seed file |
| `batch_size` | `500` | Work IDs per batch |
| `start_batch` | `1` | First batch to process |
| `end_batch` | `68` | Last batch (computed from 33,693 unique work IDs ÷ 500 = ~68 batches) |
| `merge_policy` | `restore_merge` | Restore from HF then merge, or replace local |
| `min_seconds_between_requests` | `1.0` | API pacing in seconds |
| `max_parallel` | `2` | Parallel batch jobs (when serial=false) |
| `serial` | `false` | Process batches sequentially in one runner |
| `max_works` | `none` | Optional sync limit |

### Jobs:
1. **plan** — Reads seed file, validates, splits into batch files, computes SHA-256 hashes, writes provenance JSON, uploads batch artifact
2. **batch** (parallel, when `serial=false`) — Fans out across runners, restores live HF state, syncs batch, validates, manifests, coverage-report, uploads batch artifact
3. **serial** (when `serial=true`) — Processes all batches sequentially in one runner, cumulative `data/` directory

### Post-sync validation gates:
- `uv run nzlc validate` — blocks on errors
- `uv run nzlc manifest` — builds `latest_manifest.json` and `latest_changes.json`
- `uv run nzlc coverage-report` — writes `coverage_report.json` and appends to `coverage_history.jsonl`

### Review artifacts (from each batch):
- `data/_state/sync_state.json` — failed-version warnings
- `data/manifests/validation_report.json`
- `data/manifests/latest_manifest.json`
- `data/manifests/coverage_report.json`

---

## 4. Historical Bootstrap Context

### Dataset split:
- **Live**: `edithatogo/corpus-legislation-nz` — daily API-discovery corpus
- **Historical**: `edithatogo/corpus-legislation-nz-historical` — reviewed batch uploads

### Current historical progress (from `historical_completeness_plan.md`):
- Batch 0001: Confirmed, 5,173 records, revision `dcc92964ef832c7e0bd2f904f88de523998304f2`
- Batch 0002: Confirmed, 5,779 records, revision `bb425cb308410fac43095a30f88c9d92848a0eb8`
- Batch 0003: Confirmed, 6,384 records, revision `0cc4021cae106c0b9ae3722488faed21df3e578c`
- Batch 0004: Confirmed, manifest SHA-256 `c00b6d316c423738206a92ca5c18abafdcde79fd7288b9cb30e120d0e619709c`
- Batch 0005: Confirmed
- Batch 0006: Confirmed (in progress run `27382946724`)
- Batch 0007: No-upload pending (run `27383069057`)
- Batches 0005-0068: Seeds promoted to `main` in `seeds/reviewed/`
- **Total unique work IDs in seed**: 33,693
- **Seed SHA-256**: `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`

### Relevant workflows for historical processing:
| Workflow | Purpose |
|----------|---------|
| `historical_batch_review.yml` | Parallel batch fan-out for no-upload validation on GitHub-hosted runners |
| `historical_hf_upload.yml` | Serial confirmed upload to historical HF dataset |
| `historical_seed_reconciliation.yml` | Compare candidate vs baseline seeds before promotion |
| `historical_sync_pilot.yml` | Bounded discovery + sync pilot |
| `historical_work_id_discovery.yml` | Broad API-discovery of work IDs |
| `init_historical_hf_shell.yml` | Initialize historical HF dataset shell |

---

## 5. Scheduled Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `hf_sync.yml` | Daily (`17 14 * * *`) | Live corpus sync + HF upload |
| `doctor.yml` | Weekly | Non-destructive connectivity/config check |
| `monthly_full_reconciliation.yml` | Monthly | Seed reconciliation, optional full sync/upload |
| `annual_zenodo_archive.yml` | Annual | Production draft archive + optional publish |

---

## 6. Validation Governance (from `docs/schema_governance.md`)

### Blocking failures (upload blockers):
- Duplicate `stable_id` or `version_id`
- Missing required fields
- Empty `text` (unless `--allow-empty-text`)
- `text_sha256` mismatch
- JSON Schema validation errors
- `record_schema_version` mismatch

### Informational warnings (non-blocking):
- Missing XML URL when another format is available
- Ephemeral identifiers (`id_is_ephemeral`)

### Coverage report risk indicators:
- `missing_text_records`
- `missing_xml_url_records`
- `ephemeral_identifier_records`

---

## 7. Key Decision Log (Extracted from docs)

1. **First bootstrap on controlled runner**: Not on GitHub Actions due to unknown corpus size; use local/self-hosted with ≥25GB free disk
2. **Deterministic seed over search**: Seed files are safest; search terms are convenience for discovery
3. **Historical != Live**: Separate HF datasets; guard script prevents accidental upload to live
4. **XML-to-HTML fallback**: Early local/imperial Acts have XML 404s; HTML fallback remediates this
5. **restore_merge only for incremental**: Confirmed incremental uploads MUST use `restore_merge` to avoid pruning published data
6. **review → confirm workflow**: No-upload review first, then confirmed upload with `upload_confirmed=true`
7. **Content SHA-256 comparison**: Upload skipped when remote manifest content hash matches local

---

## 8. CLI Command Reference for Bootstrap

```bash
# Sync with seed work IDs (deterministic bootstrap)
uv run nzlc sync --seed-work-ids seeds/work_ids.txt --allow-no-search-terms

# Validate records against JSON Schema
uv run nzlc validate

# Build manifest (content hashing)
uv run nzlc manifest

# Coverage report (by type/status/year, risk indicators)
uv run nzlc coverage-report

# Discover work IDs from search terms
uv run nzlc discover-work-ids --search-terms "act,bill" --output-path seeds/discovered.txt

# Split seed into deterministic batches
uv run nzlc split-work-id-batches --seed-work-ids seeds/work_ids.txt --batch-size 500

# Reconcile two seed inventories
uv run nzlc reconcile-work-ids --baseline-work-ids seeds/baseline.txt --candidate-work-ids seeds/candidate.txt

# Upload to Hugging Face
uv run nzlc hf-upload
```