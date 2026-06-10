# SOTA Metadata Packages

Date: 2026-06-11.

This document records the Track 30 implementation for generated Croissant,
RO-Crate, Frictionless, DCAT, and PROV-O metadata packages.

## Decision

Metadata packages are generated artifacts, not hand-edited release files. The
repo now provides:

- generator: `src/nz_legislation_corpus/metadata_packages.py`;
- CLI generation command:
  `uv run nzlc metadata-packages --output-dir generated/metadata-packages`;
- CLI validation command:
  `uv run nzlc validate-metadata-packages --metadata-dir generated/metadata-packages`;
- focused tests: `tests/test_metadata_packages.py`.

Generated outputs are written under `generated/metadata-packages` by default.
The `generated/` directory is ignored by Git, so package files are recreated
from canonical inputs during release preparation.

## Generated Files

| File | Metadata family | Purpose |
| --- | --- | --- |
| `croissant.json` | Croissant | ML-ready dataset discovery metadata for the Hugging Face live dataset. |
| `ro-crate-metadata.json` | RO-Crate | Research-object package metadata tying dataset, schemas, GitHub, and Zenodo. |
| `datapackage.json` | Frictionless | Tabular/data-resource descriptor for JSONL and Parquet resources. |
| `dcat.jsonld` | DCAT | Catalog/distribution metadata for public data portals and future linked-data catalogs. |
| `prov-o.jsonld` | PROV-O | Provenance graph for generated metadata and source-manifest dependency. |
| `metadata-package-manifest.json` | Project manifest | File checksums, validation result, source-manifest reference, publication links, and rights note. |
| `SHA256SUMS.txt` | Checksums | SHA-256 checksums for all generated package files and the package manifest. |

## Inputs

The generator uses repo-local canonical inputs:

- `schemas/shared_nz_corpus_core.schema.json`;
- `schemas/legislation_record.schema.json`;
- `data/manifests/latest_manifest.json` when present;
- otherwise the shared core schema hash as a local no-data source-manifest
  fallback;
- current public-surface URLs recorded in Track 26;
- rights-scope language from Track 27;
- corpus-family labels from Tracks 24 and 29.

This means local validation works before a full corpus manifest exists, while a
real release run automatically binds generated packages to
`data/manifests/latest_manifest.json`.

## Validation Contract

Validation currently checks:

- every expected metadata package exists;
- every package is valid JSON;
- required family-specific top-level keys exist;
- the shared NZ corpus core schema is valid Draft 2020-12 JSON Schema;
- the package manifest contains per-file checksums, publication-surface links,
  source-manifest reference, coverage status, and rights note.

Full external validators for Croissant, RO-Crate, Frictionless, DCAT, and PROV-O
can be added in later tracks without changing the generated-file contract.

## Publication Surfaces

GitHub:

- Stores generator, validator, docs, schemas, and tests.
- Does not store generated package outputs except tiny fixtures if a later test
  needs them.

Hugging Face:

- Suitable target for generated metadata packages after release validation.
- Packages must remain tied to the live dataset revision or manifest hash.

Zenodo:

- Suitable for immutable annual snapshots if the archive policy includes these
  package files.
- Existing DOI records and immutable archive filenames must not be changed by
  this track.

OSF:

- Inactive. OSF metadata-package mirrors require a future mirror/review policy.

Future metadata endpoints:

- Croissant, RO-Crate, Frictionless, DCAT, and PROV-O packages should reference
  `schemas/shared_nz_corpus_core.schema.json` and preserve both
  `corpus-nz-legislation` and `corpus-nz-hansard` family labels.

## Release Use

Before publishing generated metadata packages:

1. Generate or restore the intended corpus data and manifest.
2. Run `uv run nzlc manifest`.
3. Run `uv run nzlc metadata-packages --output-dir generated/metadata-packages`.
4. Run
   `uv run nzlc validate-metadata-packages --metadata-dir generated/metadata-packages`.
5. Review `generated/metadata-packages/metadata-package-manifest.json`.
6. Publish only through an explicit release/upload/archive workflow.
