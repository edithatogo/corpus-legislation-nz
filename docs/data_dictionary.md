# Data dictionary

This dictionary summarizes the stable record fields defined in `schemas/legislation_record.schema.json`. Parquet output omits `raw_version_metadata` by default to keep the analytical table compact.

For generated cross-corpus metadata and endpoint exports, see the shared NZ
corpus core schema in `docs/shared_nz_corpus_core_schema.md` and
`schemas/shared_nz_corpus_core.schema.json`. That shared schema is a
compatibility layer; it does not replace this legislation record schema.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `record_schema_version` | string | yes | Public record schema version. Current value: `1.0`. |
| `stable_id` | string | yes | Stable pipeline identifier for the normalized version record. |
| `work_id` | string | yes | NZ Legislation work identifier. |
| `version_id` | string | yes | NZ Legislation version identifier. |
| `title` | string | yes | Legislation title from the source metadata. |
| `jurisdiction` | string | yes | Constant value: `New Zealand`. |
| `country` | string | yes | Constant value: `NZ`. |
| `source` | string | yes | Source system label. |
| `source_url` | string | yes | Human-readable source URL where available. |
| `api_url` | string | yes | API URL for the source version metadata. |
| `xml_url` | string | no | XML format URL where available. |
| `html_url` | string | no | HTML format URL where available. |
| `pdf_url` | string | no | PDF format URL where available. |
| `legislation_type` | string | yes | Source legislation type used for filtering and Parquet partitioning. |
| `legislation_subtype` | string | no | More specific source subtype where available. |
| `legislation_status` | string | yes | Source status value, such as current or historical. |
| `version_date` | string | no | Version date from the source metadata where available. |
| `year` | integer or null | no | Year derived from source metadata; used for Parquet partitioning. |
| `scrape_date` | string | yes | Date the source was scraped or normalized. |
| `ingest_timestamp_utc` | string | yes | UTC timestamp for ingestion. |
| `administering_agencies` | array of strings | no | Administering agencies listed in the source metadata. |
| `is_latest_version` | boolean | no | Whether the source indicates this is the latest version. |
| `language` | string | yes | Record language code or label. |
| `text` | string | yes | Conservatively extracted legislation text. |
| `raw_xml_sha256` | string | no | SHA-256 hash for raw XML when available. |
| `raw_content_sha256` | string | no | SHA-256 hash for raw source content. |
| `text_sha256` | string | yes | SHA-256 hash of extracted text. |
| `source_hash` | string | yes | Stable source-content hash used to detect changes. |
| `pipeline_version` | string | yes | Pipeline version or commit identifier used for ingestion. |
| `id_is_ephemeral` | boolean | no | Whether the identifier is treated as ephemeral. |
| `id_ephemeral_reason` | string | no | Reason an identifier was marked ephemeral. |
| `raw_version_metadata` | object | no | Raw source metadata retained in JSONL, omitted from Parquet by default. |

## Partitioning

Parquet files are written under:

```text
parquet/legislation_type=<type>/year=<year>/part-00000.parquet
```

Partition values are normalized to lowercase path-safe strings. Missing values use `unknown`.
