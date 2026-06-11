# Implementation status

Last reconciled: 2026-06-11.

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
- Broad no-limit historical work-ID discovery passed in GitHub Actions run
  `27313765016`, producing 33,693 unique search-derived candidate work IDs.
- The broad candidate was reconciled against the reviewed 10-work historical
  pilot seed with 33,683 additions and 0 removals, then split locally into 68
  deterministic 500-work batches for no-upload validation planning.
- First reviewed 500-work historical batch no-upload validation passed in
  GitHub Actions run `27316467370` with `upload_confirmed=false`; validation
  reported 4,737 restored/merged records and manifest SHA-256
  `19e5f5c8eb25307d170105659d20d459a42fea8668eb424223abc40b844bea51`.
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
- The 33,693-work historical inventory is search-derived and still requires
  external or authoritative reconciliation before any full-completeness claim.
- The live Hugging Face dataset is intentionally partial/API-discovery based.
- The historical Hugging Face dataset is a successful bootstrap, not a complete
  historical corpus.
- The first reviewed 500-work historical no-upload batch found 436 failed
  versions, mostly 404 XML responses for early local/imperial Acts. Confirmed
  upload of that batch should wait until those failures are triaged or
  documented as accepted exclusions.
- The first scheduled-run gate for public launch was explicitly waived by the
  repository owner on 2026-06-09; manual live sync and publication evidence
  exist, but scheduled maintenance still needs continuing evidence.
- Published Zenodo archive filenames still contain the old launch prefix because
  those files are part of the immutable DOI snapshot.

## Next maintainer actions

1. Triage the 436 failed versions from no-upload historical run `27316467370`
   before confirming upload of reviewed batch 0001.
2. Review the 33,693-work search-derived candidate inventory and decide whether
   to seek an official work-ID export before promotion.
3. Promote or revise the candidate seed only after external/authoritative
   reconciliation resolves the remaining completeness gap.
4. Continue roadmap implementation for data-quality dashboarding, structural XML
   extraction, published metadata packages, and long-term maintenance evidence.
