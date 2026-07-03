# Source redundancy resolver

The canonical ingestion path remains the official NZ Legislation API. Redundant
sources are used to detect freshness gaps, recover failed public records, or
corroborate coverage. They do not change public completeness claims until their
evidence is reconciled.

The resolver priority is:

1. API XML
2. Official HTML
3. Alternate dated official URL
4. Official website fallback
5. NZLII candidate or rescue

Each retrieval attempt should record source name, URL, method, timestamp,
status, content hash, warning or error text, confidence, and rights notes. The
selected resolver decision must state whether the record is canonical or needs
manual review.

Secondary or browser-derived fallbacks are review evidence first. Promotion into
canonical records requires an explicit review path and source-rights caveats.

The machine-readable decision schema is
`schemas/source_redundancy.schema.json`. Normalized records can carry the
decision under `source_redundancy`; full-bootstrap review reports summarize the
same structure under `source_redundancy` with status counts, selected-method
counts, confidence counts, canonical/fallback totals, and manual-review IDs.

## Track Coordination

Track 37 feed change detection emits advisory refresh signals into the
canonical API-first queue. Feed observations detect that something may need
refreshing; they do not become source text and do not override API results.

Track 38 official website fallback retrieval supplies official-site fallback
evidence after API XML, advertised HTML, and alternate dated URL attempts fail.
Rendered browser output is low-confidence diagnostic evidence unless a reviewer
approves a specific promotion path with provenance preserved.

Track 39 NZLII redundancy reconciliation supplies secondary corroboration,
coverage comparisons, and text-rescue triage candidates. NZLII evidence remains
non-canonical and review-only unless a future approved policy explicitly permits
promotion.

Track 48 Gazette freshness and change detection turns official and DigitalNZ
change signals into deterministic refresh queues for Tracks 42-46. Freshness
signals remain advisory evidence and do not replace the immutable source
archives or the canonical comparison layer.

None of these tracks override official-source primacy without explicit manual
review. Fallback-assisted or NZLII-derived records remain non-canonical until a
human reviewer records approval and the source-specific rights caveat is
preserved in sync state, review reports, manifests, and public-facing metadata.

Neither Track 38 nor Track 39 evidence may be used to claim corpus completeness.
Public coverage language stays limited to the verified scope until
reconciliation evidence proves the boundary. Resolver outputs should set shared
core `coverage_status` conservatively, using `partial`, `search_derived`, or
`unknown` unless a reviewed authoritative inventory supports `complete`.
