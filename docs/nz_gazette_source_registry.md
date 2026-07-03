# NZ Gazette Source Registry

Date: 2026-07-03.

This document defines the shared source contract for the New Zealand Gazette
archive family. It exists so the raw source layers can be archived separately
while the canonical Gazette layer remains a derived comparison output.

The machine-readable registry lives at
`docs/nz_gazette_source_registry.json` and is validated by
`schemas/nz_gazette_source_registry.schema.json`.

## Source Registry

| source_id | source_tier | base_url | canonical_eligible | rights and access note |
| --- | --- | --- | --- | --- |
| `official_gazette` | `official` | `https://gazette.govt.nz/issues` | yes | Preferred canonical evidence when public issue pages or PDFs are available. Respect public-access limits and fail closed on bot protection or access-control bypass. |
| `digitalnz_gazette` | `discovery` | `https://digitalnz.org/` | corroborating only | DigitalNZ metadata and full text are source evidence, not canonical truth. Use the local `dnz` exporter or equivalent bounded, resumable query path. |
| `victoria_lexisnexis_gazette` | `historical` | `https://library.victoria.ac.nz/databases/nzgazettearchive/Html/2008.html` | historical only | Historical coverage and rights notes must stay attached to every record. Treat as secondary evidence unless explicit comparison evidence says otherwise. |
| `nzlii_gazette` | `redundancy` | `https://www.nzlii.org/` | fallback only | Use only if robots, access, and coverage checks pass. Record blocked/unavailable states explicitly. |

## Retrieval Policy

- Requests must be identifiable, conservative, and rate-limited.
- Stealth scraping, CAPTCHA bypass, and access-control bypass are not permitted
  archive mechanisms.
- Source-specific smoke runs must remain bounded and resumable.
- Raw source captures must preserve request/response metadata where available,
  including headers and response status.

## Coverage Matrix

The coverage matrix records source coverage by:

- `source_id`
- `year`
- `issue_id`
- `notice_id`
- `page_start`
- `page_end`
- `artifact_type`
- `coverage_state`

The machine-readable registry exposes this as `coverage_matrix`, with the
dimension keys above.

Coverage states are:

- `complete`
- `partial`
- `gap`
- `overlap`
- `blocked`
- `unknown`

## Canonical Precedence

When source comparison is possible, the canonical builder should prefer:

1. `official_gazette`
2. `digitalnz_gazette`
3. `victoria_lexisnexis_gazette`
4. `nzlii_gazette`

The machine-readable registry stores this ordering in
`canonical_precedence`.

That precedence only applies after comparing raw source evidence and recording
conflicts. Raw archives remain immutable evidence layers.

## Shared Raw Archive Contract

Every source-specific raw record must include:

- stable record ID
- source ID
- source name
- source tier
- source URL
- retrieval method
- retrieval timestamp
- content hash
- raw artifact path
- rights note
- source-local identifier
- provenance object

## Shared Canonical Contract

Every canonical Gazette record must include:

- canonical record ID
- canonical URI
- canonical source
- supporting sources
- conflicts
- confidence
- normalization version
- rights note
- provenance links back to source archive records

## Downstream Track Contract

Tracks 47 and 48 are the immediate downstream follow-on tracks after the
shared registry is defined.

- Tracks 42-47 implement the source and canonical layers:
  - Track 42 archives the official Gazette source layer.
  - Track 43 archives the DigitalNZ source layer.
  - Track 44 archives the Victoria/LexisNexis historical source layer.
  - Track 45 archives the NZLII redundancy source layer or records a blocked
    source state.
  - Track 46 builds the derived canonical layer from the independent source
    archives.
  - Track 47 adds the workflow, review, and publication staging around those
    layers.
