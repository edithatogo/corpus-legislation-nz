# NZ Gazette Archive Plan

## Purpose

Add the New Zealand Gazette as a multi-source archive with separate raw source
layers and a derived canonical layer.

The shared registry and schema contract for this track lives in:

- `docs/nz_gazette_source_registry.md`
- `docs/nz_gazette_source_registry.json`
- `schemas/nz_gazette_source_registry.schema.json`
- `schemas/nz_gazette_raw_source_record.schema.json`
- `schemas/nz_gazette_canonical_record.schema.json`

## Source Tiers

1. Official Gazette site:
   `https://gazette.govt.nz/issues`
2. Victoria University historical archive:
   `https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html`
3. DigitalNZ Gazette discovery/export
4. NZLII redundancy archive

## Core Rules

- Archive each source separately.
- Treat raw source captures as immutable evidence.
- Build canonical Gazette records only by comparing the source layers.
- Preserve provenance on every canonical record.
- Keep rights, access, and retrieval limits attached to each source archive.

## Canonical Inputs

- issue number
- publication date
- notice title
- page number
- source URL
- content hash
- source-specific extraction metadata

## Tooling Note

A quick search of the current repo and nearby `edithatogo` repos initially did
not reveal a Gazette-specific CLI to reuse. Track 43 now uses a corpus-side
DigitalNZ Gazette export wrapper and records the reusable-exporter gap in
`edithatogo/dnz` issue #1 so the dependency can be hardened without blocking
the archive work.

## Implementation Contract

Tracks 42-47 must treat the registry, raw archive schema, and canonical schema
as the shared contract for all Gazette source work. Raw source archives remain
independent evidence layers; canonical records remain derived outputs that are
reproducible from source manifests and review evidence.
