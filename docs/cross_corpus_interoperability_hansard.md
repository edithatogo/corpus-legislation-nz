# Cross-Corpus Interoperability With Hansard

Date: 2026-06-10.

This note records how `corpus-legislation-nz` should reuse interoperability
patterns from sibling project `corpus-nz-hansard` without changing the
legislation corpus into a Hansard-style parliamentary proceedings dataset.

This is a roadmap contract. It does not implement endpoint exporters, replace
the core record schema, or add heavy dependencies to the base install.

## Hansard Reference Patterns

The Hansard checkout reviewed for this track is:

`C:\Users\60217257\OneDrive - Flinders\repos\corpus-nz-hansard`

Reference documents and track patterns:

- `docs/search-rag-index-contract.md`
- `docs/rdf-linked-data-mapping.md`
- `docs/akoma-ntoso-mapping.md`
- `docs/endpoint-contracts.md`
- `docs/interoperability-design.md`
- `docs/interoperability-requirements-moscow.md`
- `docs/sota-metadata-packages.md`
- `docs/shared-nz-corpus-core-schema.md`
- `docs/duckdb-analysis.md`
- `docs/generated-output-policy.md`
- `docs/canonical-id-uri-policy.md`
- `docs/osf-optional-mirror-policy.md`

The Hansard checkout was used as a reference source only. It was not modified by
this track.

## Applicability Matrix

| Pattern | Legislation decision | Governance requirement |
| --- | --- | --- |
| DuckDB and Polars access examples | Applicable now for Hugging Face Parquet and local Parquet inspection. | Keep examples dependency-light and researcher-facing; do not add runtime dependencies to the base package. |
| Search/RAG index contract | Applicable as an optional generated artifact. | Must include stable record identifiers, work/version identifiers, source URL, text hash, manifest hash, Hugging Face revision, coverage caveat, and citation/provenance fields. |
| RDF, DCAT, and PROV-O | Applicable as future metadata and linked-data surfaces. | Generate from validated records and manifests; do not replace the core schema. Use stable URI policy and source-manifest references. |
| Croissant metadata | Applicable for ML-ready dataset discovery. | Generate and validate as a metadata package in a separate track before publication. |
| RO-Crate | Applicable for research-object packaging, especially fixed release snapshots. | Include data files, manifests, checksums, citation metadata, license/source-rights notes, and generation evidence. |
| Frictionless Data Package | Applicable for tabular schema and resource descriptors. | Must point to versioned Parquet/JSONL resources and validate against the current schema. |
| Akoma Ntoso | Applicable only as a generated legal-document export endpoint. | Do not make Akoma Ntoso the internal schema. Preserve original NZ Legislation source references and generated-export provenance. |
| Endpoint contracts | Applicable for every optional derived artifact. | Each endpoint must be versioned, checksummed, validated, and explicitly optional. |
| OSF mirror/review bundle | Optional, policy-gated. | Use only after file layout, citation, and synchronization policy are explicit. |

Hansard-specific patterns that should not be copied into the legislation core
schema include speech turns, member identity, party attribution, parliamentary
proceeding structure, votes, motions, oral questions, ParlaMint, Popolo or
OpenCivicData parliamentary actor fields, and linguistic exports such as UD
CoNLL-U or NIF unless a later NLP track deliberately scopes them.

## Shared Core Boundary

The shared corpus-family layer should focus on fields that are meaningful across
both legislation and Hansard:

- corpus family name and publication target.
- stable record identifier.
- source system and source URL.
- title or display label.
- date fields with declared semantics.
- text hash and manifest hash.
- schema version.
- generation command and software revision.
- coverage/completeness statement.
- citation and rights metadata.

Dataset-specific fields remain in dataset-specific schemas. For legislation,
the primary grain is a versioned legal instrument or instrument version. For
Hansard, the primary grain is a parliamentary speech, sitting, or proceeding
unit. Track 29 defines the exact shared core fields and compatibility
expectations in `docs/shared_nz_corpus_core_schema.md` and
`schemas/shared_nz_corpus_core.schema.json`.

## Optional Artifact Contract

Every optional derived artifact must have:

- A stable artifact name and semantic version or dataset release version.
- A generation command and tool version.
- The source manifest hash and, where applicable, Hugging Face dataset revision.
- A checksum for every produced file.
- A validation report or schema-conformance report.
- A coverage boundary that states whether the artifact is full, partial,
  sample, pilot, or search-derived.
- Citation guidance matching GitHub, Hugging Face, Zenodo, OSF, and any future
  metadata endpoint.
- A publication policy that says whether the artifact is committed to GitHub,
  uploaded to Hugging Face, archived on Zenodo, mirrored on OSF, or held locally.

Generated endpoint artifacts must not be treated as authoritative source data.
The authoritative reconstruction path remains source API or source XML/HTML,
normalized records, Parquet, manifests, and validation reports.

## Publication Surface Policy

| Surface | Role for interoperability artifacts |
| --- | --- |
| GitHub | Code, docs, schemas, tests, contracts, and small validation fixtures. Avoid large generated artifacts. |
| Hugging Face | Operational dataset files and optional machine-readable derived artifacts after validation. |
| Zenodo | Immutable release snapshots and metadata packages only when included in an approved release/archive policy. |
| OSF | Optional review or mirror bundles only after explicit policy approval. |
| Future metadata endpoints | Croissant, RO-Crate, Frictionless, DCAT, PROV-O, and related discovery files generated from validated manifests. |

Publication metadata must keep the preferred family label
`corpus-nz-legislation`, the current public dataset line
`corpus-legislation-nz`, and sibling reference `corpus-nz-hansard` aligned.

## Roadmap Placement

This track establishes the cross-corpus roadmap only. Implementation belongs in
follow-up tracks:

- Track 29: define the shared NZ corpus core schema.
- Track 30: generate and validate Croissant, RO-Crate, Frictionless, DCAT, and
  PROV-O metadata packages.
- Track 33: add release evidence ledgers, checksums, and provenance
  attestations.
- Future endpoint tracks: implement optional search/RAG, RDF, Akoma Ntoso, or
  other derived exports after their contracts and validation gates are explicit.
