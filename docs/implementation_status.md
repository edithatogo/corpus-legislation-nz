# Implementation status

Last reconciled: 2026-06-10.

## Implemented

- API-first NZ Legislation client with X-Api-Key auth, request pacing, low-quota
  backoff, retries, 429 handling, and conservative 403 burst-limit handling.
- Configurable discovery via search terms and/or seed work IDs.
- XML/HTML text extraction.
- Normalized record schema and validation report.
- Deterministic partitioned Parquet writer with PyArrow content-defined chunking
  and page-index options when supported.
- Stable content hashing in manifests. Generated timestamps and local state do
  not force uploads.
- Unchanged records are preserved byte-for-byte so scrape timestamps do not
  churn `records.jsonl` or Parquet.
- Hugging Face upload wrapper using `hf upload-large-folder` with fallback to
  `HfApi.upload_folder`.
- Hugging Face upload path uses `HF_XET_HIGH_PERFORMANCE=1`.
- Zenodo draft/new-version/archive upload client using bucket uploads where
  available.
- `nzlc coverage-report` for corpus coverage and risk indicators.
- `nzlc reconcile-work-ids` for candidate/baseline seed reconciliation before
  historical seed promotion.
- Ephemeral NZ Legislation identifiers containing `~` are explicitly flagged.
- GitHub Actions for live sync, historical upload, annual Zenodo archive, weekly
  doctor, tests, CodeQL, and OpenSSF Scorecard.
- Manual GitHub Actions workflow for historical seed reconciliation.
- Dependabot config.
- GitHub CLI bootstrap scripts for creating a fresh repository and configuring
  Actions secrets/variables.
- Manual first-sync guardrails for `max_works=5` and increased request spacing
  in the bootstrap docs and workflow dispatch input.
- Conductor tracks, contracts, red-team review, prioritized recommendations,
  setup docs, security policy, and maintenance runbook.

## Live publication status

- GitHub repository: `https://github.com/edithatogo/corpus-legislation-nz`.
- GitHub release/tag:
  `https://github.com/edithatogo/corpus-legislation-nz/releases/tag/v0.1.0-partial.20260609`.
- Live Hugging Face dataset:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Current verified live Hugging Face revision:
  `6b082e2f85802cb374898d689d264017a047799b`.
- Historical Hugging Face dataset:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical`.
- Current verified historical Hugging Face revision:
  `901a2ecc03e260758dc72bf965607a74a7417221`.
- Zenodo production record: `https://zenodo.org/records/20592540`.
- Zenodo DOI: `10.5281/zenodo.20592540`.
- Public-surface evidence ledger:
  `docs/public_surface_evidence_ledger.md`.
- Naming/publication alignment decision:
  `docs/naming_publication_alignment.md`.
- Hansard interoperability roadmap:
  `docs/cross_corpus_interoperability_hansard.md`.
- Zenodo rights and zenodraft workflow decision:
  `docs/zenodo_rights_metadata_zenodraft.md`.
- GitHub repository-name migration assessment:
  `docs/github_repository_name_migration_assessment.md`.
- Shared NZ corpus core schema:
  `docs/shared_nz_corpus_core_schema.md`.
- SOTA metadata package generator:
  `docs/sota_metadata_packages.md`.

## Validated locally or through live workflows

- Python source compilation, workflow YAML parsing, unit tests, and Ruff checks
  have passed in earlier implementation tracks.
- Credential-free local smoke fixture passed through validation, manifest
  generation, coverage reporting, and archive creation.
- Live partial/API-discovery Hugging Face upload passed and produced a
  six-record public dataset.
- Hugging Face restore/no-change behavior was proven for the partial launch.
- Zenodo production publication passed for the approved partial launch snapshot.
- Historical Hugging Face bootstrap publication passed for a reviewed
  search-derived 500-work bootstrap.
- Historical seed reconciliation is implemented locally and in a manual
  no-upload workflow.
- Naming/publication alignment is documented for the preferred
  `corpus-nz-legislation` family label while preserving the current
  `corpus-legislation-nz` public surfaces.
- Cross-corpus interoperability with `corpus-nz-hansard` is documented as a
  roadmap contract covering DuckDB/search/RAG, linked data, generated metadata
  packages, Akoma Ntoso export considerations, endpoint validation, and
  publication-surface policy.
- Zenodo rights scope and future `zenodraft` adoption are documented; the
  current workflow remains draft-first and production publish remains protected.
- GitHub repository-name migration is assessed but not executed; the preferred
  name should be reserved as a pointer before any full live rename.
- Shared core schema compatibility with `corpus-nz-hansard` is documented and
  validated without replacing the legislation-specific record schema.
- Croissant, RO-Crate, Frictionless, DCAT, and PROV-O metadata packages are
  generated and validated locally as ignored release artifacts.

## Current limitations

- No authoritative `seeds/work_ids.txt` exists, so full New Zealand legislation
  coverage is not proven.
- The live Hugging Face dataset is intentionally partial/API-discovery based.
- The historical Hugging Face dataset is a successful bootstrap, not a complete
  historical corpus.
- The first scheduled-run gate for public launch was explicitly waived by the
  repository owner on 2026-06-09; manual live sync and publication evidence
  exist, but scheduled maintenance still needs continuing evidence.
- Published Zenodo archive filenames still contain the old launch prefix because
  those files are part of the immutable DOI snapshot.

## Next maintainer actions

1. Reconcile Conductor tracks against the completed partial launch and remaining
   full-completeness blockers.
2. Generate or obtain the stable full work-ID inventory.
3. Reconcile any candidate historical inventory with `nzlc reconcile-work-ids`,
   then split the reviewed historical seed into deterministic batches and run
   no-upload validation before confirmed incremental uploads.
4. Continue the roadmap tracks for shared schema, metadata packages, versioning,
   CI quality tooling, and provenance attestations.
