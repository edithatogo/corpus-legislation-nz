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
