# Versioning and release automation

This project separates code releases, dataset snapshots, schemas, publication
revisions, and evidence hashes. A single SemVer value is not reused for all of
them because they change for different reasons.

## Current state

The repository has an approved partial/API-discovery public launch, a live
Hugging Face dataset, a published Zenodo DOI snapshot, and separate historical
Hugging Face target. Full corpus completeness is still blocked by the absence of
an authoritative full seed list.

The preferred corpus-family label is `corpus-nz-legislation`, aligned with
`corpus-nz-hansard`. The current public GitHub and Hugging Face publication
line remains `corpus-legislation-nz` until a separate migration operation proves
redirects, citations, and compatibility surfaces.

## Version authorities

| Authority | Source of truth | Current value | Notes |
| --- | --- | --- | --- |
| Code/package version | `pyproject.toml` `[project].version` | `0.5.0` | Mirrored by `src/nz_legislation_corpus/__init__.py`. This version governs the Python package and CLI behavior. |
| Dataset citation version | `CITATION.cff` `version` and public launch docs | `0.1.0` | This governs the approved partial/API-discovery dataset citation, not the Python package. |
| GitHub release tag | GitHub release plus launch docs | `v0.1.0-partial.20260609` | Records the partial launch. Future full releases should use stable dataset tags such as `vMAJOR.MINOR.PATCH` only after coverage is proven. |
| Record schema version | `src/nz_legislation_corpus/schema.py` and `schemas/legislation_record.schema.json` | `1.0` | Breaking record-field changes require a new schema version and migration notes. |
| Shared NZ core schema | `schemas/shared_nz_corpus_core.schema.json` and `docs/shared_nz_corpus_core_schema.md` | shared core v1 contract | Cross-corpus compatibility surface for `corpus-nz-legislation` and `corpus-nz-hansard`. |
| Metadata package version | `src/nz_legislation_corpus/metadata_packages.py` | `0.1.0` | Covers Croissant, RO-Crate, Frictionless, DCAT, and PROV-O package shape. |
| Hugging Face revision | `docs/public_surface_evidence_ledger.md` | evidence-ledger value | A moving Git commit/revision on the dataset repository; cite with access date and manifest hash for live use. |
| Zenodo DOI snapshot | `CITATION.cff`, dataset card, README, and Zenodo ledger | `10.5281/zenodo.20592540` | Immutable citation target for the approved partial launch. Zenodo draft operations use the annual workflow today; `zenodraft` was evaluated in Track 27. |
| Manifest hash | `data/manifests/latest_manifest.json` when generated | run-specific | Required for dataset release evidence. It is absent before a validated corpus run and must not be invented. |

## Release automation decision

Release Please, or an equivalent Conventional Commits changelog/tag workflow, is
deferred for now.

Reasons:

- the live dataset is intentionally partial and must not be promoted by a code
  release workflow;
- Hugging Face and Zenodo publication must remain behind validation gates and
  explicit operator approval;
- package releases, dataset releases, schema changes, and Zenodo snapshots have
  separate version authorities;
- protected-environment proof and publication gate evidence are still stronger
  requirements than automated tagging.

The future automation contract is:

- Conventional Commits may drive package changelog proposals;
- release automation may open a PR that updates package release notes and
  version-bearing files;
- release automation must not upload to Hugging Face or publish Zenodo records;
- dataset publication workflows must require manual dispatch, validation
  outputs, manifest hashes, and protected environment approval where applicable;
- Zenodo production publication must remain draft-first and reviewer-gated.

## Consistency checks

`scripts/check_version_consistency.py` is the local and CI check for the current
version model. It validates:

- `pyproject.toml` package version matches `src/nz_legislation_corpus/__init__.py`;
- record schema constants match between Python and JSON Schema;
- version-bearing values use expected SemVer-like formats;
- the Zenodo DOI is present on the public citation surfaces;
- the approved partial-launch release tag is recorded on release evidence
  surfaces;
- this document records the separate authorities and deferred Release Please
  decision;
- generated manifest files, when present, include expected hash and schema
  fields.

Run it locally with:

```powershell
uv run python scripts\check_version_consistency.py
```

The GitHub `Tests` workflow also runs the check with read-only repository
permissions. The check is evidence-only: it fails inconsistent text or metadata,
but it does not publish, tag, upload, or mutate external services.

## Dependency update policy

Routine dependency PRs are handled by Renovate with no automerge. Dependency
updates must not trigger Hugging Face uploads or Zenodo publication. Publication
workflows are manual or protected, and dependency PR validation remains limited
to tests, lint, consistency checks, and dry-run evidence.

## Future work

Track 32 owns broader Rust-backed quality tooling such as `typos`, `zizmor`,
`taplo`, and `actionlint`. Track 33 owns release provenance and artifact
attestations. This track only establishes the versioning authority model and
enforces the checks needed before those workflows become publishing gates.
