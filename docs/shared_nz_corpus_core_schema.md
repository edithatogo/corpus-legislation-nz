# Shared NZ Corpus Core Schema

Date: 2026-06-10.

This document defines the legislation-side copy of the shared NZ corpus-family
core schema. It aligns `corpus-nz-legislation` with sibling
`corpus-nz-hansard` for generated metadata packages and endpoint exports while
leaving each corpus free to keep its own canonical record schema.

The machine-readable schema is
`schemas/shared_nz_corpus_core.schema.json`.

## Scope

The shared core is a compatibility layer for identity, source provenance,
dates, canonical links, hashes, release traceability, rights notes, and coverage
status.

It is not a replacement for:

- `schemas/legislation_record.schema.json`;
- Hansard's corpus-specific document-level schema;
- Hansard speech-turn, sitting, member, party, vote, motion, or proceeding
  component schemas;
- future Akoma Ntoso, RDF, ParlaMint, Croissant, RO-Crate, Frictionless, DCAT,
  or PROV-O export schemas.

Generated endpoint work can wrap or map this core, but must not silently rename
or remove these fields once public endpoint artifacts depend on them.

## Required Core Fields

| Field | Purpose |
| --- | --- |
| `corpus_id` | Corpus-family identifier: `corpus-nz-legislation` or `corpus-nz-hansard`. |
| `record_id` | Stable record identifier within the corpus release. |
| `source_id` | Stable upstream source identity used by the corpus pipeline. |
| `jurisdiction` | Jurisdiction label. Current NZ value: `New Zealand`. |
| `country` | Country code. Current NZ value: `NZ`. |
| `document_type` | Corpus-neutral document class, such as `act`, `bill`, `secondary_legislation`, `hansard_document`, or `speech_turn`. |
| `display_title` | Human-readable title, heading, or display label. |
| `language` | Record language code or label. |
| `record_schema_version` | Version of the corpus-specific record schema used to emit the mapped record. |
| `canonical_uri` | Canonical corpus URI for generated endpoint and metadata exports. |
| `source_url` | Public source URL when available; `null` only where no direct upstream public URL exists. |
| `source_version` | Upstream version, source extract version, file revision, or equivalent version label. |
| `effective_date` | Date the record applies from, where known. |
| `published_date` | Public publication date, where known. |
| `last_modified_date` | Upstream or local last-modified date, where known. |
| `content_sha256` | SHA-256 hash of normalized content for the record. |
| `manifest_sha256` | SHA-256 hash of the release manifest that accounts for the record. |
| `coverage_status` | Completeness boundary for the mapped record set: `complete`, `partial`, `pilot`, `sample`, `search_derived`, or `unknown`. |
| `rights_note` | Short public rights/provenance note. |
| `provenance` | Object containing pipeline, source, release, and rights traceability fields. |

Date fields use `YYYY-MM-DD` when present. Hash fields are lowercase hex
SHA-256 values.

## Provenance Object

The shared `provenance` object requires:

| Field | Purpose |
| --- | --- |
| `pipeline_name` | Pipeline or builder family that emitted the record. |
| `pipeline_version` | Local pipeline version or release version. |
| `source_name` | Human-readable upstream source. |
| `source_record_id` | Upstream source record identifier. |
| `source_retrieved_at` | Retrieval timestamp, or `null` where the source package is historical/offline. |
| `release_version` | Corpus release version containing the record. |
| `release_commit` | Git commit SHA for the release. |
| `license_note` | Rights/provenance note suitable for public metadata surfaces. |

Additional corpus-specific provenance fields are allowed.

## Legislation Mapping

| Shared field | Legislation source |
| --- | --- |
| `corpus_id` | Constant `corpus-nz-legislation`. |
| `record_id` | Existing `stable_id`. |
| `source_id` | Prefer `work_id:version_id`; include both in corpus-specific fields. |
| `document_type` | Map from `legislation_type`, such as `act`, `bill`, `secondary_legislation`, or `amendment_paper`; use `instrument` or `other` only where the source value cannot be normalized. |
| `display_title` | Existing `title`. |
| `record_schema_version` | Existing `record_schema_version`, currently `1.0`. |
| `canonical_uri` | Future generated URI; should not depend on transient file paths or row positions. |
| `source_url` | Existing `source_url`. |
| `source_version` | Existing `version_id` or source version metadata. |
| `effective_date` | Existing `version_date` where it describes the operative/source version date; otherwise `null`. |
| `published_date` | Source publication date where available; otherwise `version_date` or `null` with provenance. |
| `last_modified_date` | Source modified date where available; otherwise `null`. |
| `content_sha256` | Existing `text_sha256` for text endpoints or `source_hash` for source-content endpoints; the endpoint contract must declare which one is used. |
| `manifest_sha256` | `latest_manifest.json` hash from the release that accounts for the record. |
| `coverage_status` | `partial` or `search_derived` for the current live dataset; historical bootstrap remains `partial` until full reconciliation passes. |
| `rights_note` | Rights-scope note from `NOTICE.md` and `docs/zenodo_rights_metadata_zenodraft.md`. |

The legislation core schema must not import Hansard speaker, member, party,
vote, motion, sitting, or proceeding-specific fields.

## Hansard Mapping

Hansard mapping is governed by the sibling repository's
`docs/shared-nz-corpus-core-schema.md` and
`schemas/shared_nz_corpus_core.schema.json`.

Compatibility expectations for legislation:

- accept `corpus-nz-hansard` as a peer `corpus_id`;
- allow `hansard_document`, `speech_turn`, `sitting`, and `proceeding_item`
  values in `document_type`;
- avoid assuming legislation-only identifiers such as `work_id` or
  `version_id` exist in shared generated metadata packages;
- preserve Hansard's source/extract and coverage caveats where cross-corpus
  packages combine both datasets.

## Public Surface Implications

GitHub:

- GitHub stores the schema, documentation, tests, and migration notes.
- Large generated shared-core exports should not be committed unless they are
  tiny fixtures.

Hugging Face:

- Future live or historical dataset cards should distinguish canonical
  legislation rows from shared-core generated endpoint rows.
- Shared-core endpoint artifacts must state their coverage boundary and
  manifest hash.

Zenodo:

- Zenodo DOI records remain fixed snapshots.
- Shared-core metadata may be included in future Zenodo versions only after the
  archive policy says so.
- Zenodo rights notes must not imply blanket relicensing of upstream source
  material.

OSF:

- OSF remains inactive unless a future mirror/review policy is approved.
- Any OSF bundle must use the same corpus IDs, manifest hashes, and coverage
  statements.

Future metadata:

- Croissant, RO-Crate, Frictionless, DCAT, and PROV-O packages should reference
  this schema rather than duplicating incompatible identity and provenance
  fields.

## Migration Constraints

After publication of generated shared-core artifacts, schema-breaking changes
require:

1. a migration note naming the old and new fields;
2. a compatibility window or generated compatibility view;
3. release evidence with manifest hash and Git commit;
4. updated README, dataset card, Zenodo/OSF metadata where relevant;
5. confirmation that existing GitHub, Hugging Face, and Zenodo URLs remain
   usable or have documented redirects.

The shared schema is versioned independently from the legislation corpus record
schema. A future implementation track may add generated shared-core exports, but
this Track 29 implementation only defines and validates the contract.
