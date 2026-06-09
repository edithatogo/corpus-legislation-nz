# Bleeding-Edge Versioning, CI/CD, Code Quality, and Automation Standard

## Purpose

Define the target SOTA automation standard for the NZ corpus family: `corpus-nz-legislation` and `corpus-nz-hansard`.

The target is a low-maintenance, auditable, reproducible system for package versions, dataset versions, release evidence, CI/CD, code quality, security, provenance, and publication automation.

## Versioning model

### Code/package versions

- Use SemVer for code/package APIs and CLI behaviour.
- Keep one machine-readable source of truth for package version.
- Prefer `pyproject.toml` project metadata for packaged Python projects.
- Avoid unmanaged duplicate version files unless a track explicitly synchronises them.
- Use Conventional Commits for release-note automation.
- Use Release Please or equivalent automation for changelog, tag, and GitHub release PRs.

### Dataset versions

- Treat datasets as separately versioned artifacts, not merely package versions.
- Live Hugging Face datasets are mutable operational surfaces identified by revision and manifest hash.
- Zenodo archives are immutable DOI-bearing snapshots.
- Use explicit release channels:
  - `live` for current Hugging Face state.
  - `vMAJOR.MINOR.PATCH` for stable document-level releases.
  - `YYYY` or `YYYY.N` for annual/periodic Zenodo snapshots where appropriate.
  - `review` or `rc` pre-release labels for review-stage artifacts.
- Every dataset release must record:
  - Git commit SHA.
  - Hugging Face repository and revision.
  - Zenodo DOI/concept DOI if applicable.
  - Manifest content hash.
  - Record count and coverage statement.
  - Schema version.
  - Source inventory or source-discovery method.

### Schema versions

- Version record schemas independently from code and dataset releases.
- Require migration notes for incompatible schema changes.
- Keep a cross-corpus core schema compatibility table for shared fields.

## Rust-backed and modern tooling preference

Prefer fast, low-maintenance Rust-backed tools where practical:

| Area | Preferred tool | Notes |
| --- | --- | --- |
| Python dependency/install/run | `uv` | Rust-backed; use frozen lockfiles in CI. |
| Python lint/format/imports | `ruff` | Rust-backed; replaces many Flake8/isort/format workflows. |
| Spell/identifier checks | `typos` | Rust-backed; use `crate-ci/typos` or pinned binary. |
| GitHub Actions security lint | `zizmor` | Rust-backed; audit workflow security and permissions. |
| TOML formatting/linting | `taplo` | Rust-backed; useful once pyproject/TOML config expands. |
| Search/local audit | `ripgrep` | Rust-backed; local maintenance helper, not required in CI. |
| Python type checking | `ty` | Rust-backed Astral type checker; configure all supported rules as errors for the strictest available project mode. |
| GitHub Action syntax | `actionlint` | Go-backed; still recommended because it is best-in-class. |

## CI/CD baseline

Every repository should converge on:

- Ubuntu primary CI.
- Optional Windows compatibility job only where source/archive handling requires it.
- `uv sync --frozen` for Python dependency resolution once `pyproject.toml` and lockfile exist.
- `ruff check` and `ruff format --check`.
- pytest as the test runner, even if unittest tests are still collected during transition.
- `ty check` for packaged modules with `[tool.ty.rules] all = "error"` or the strictest supported equivalent for the installed `ty` release.
- `typos` spell/identifier check.
- `zizmor` GitHub Actions security lint.
- CodeQL.
- OpenSSF Scorecard.
- Renovate for dependency and workflow updates.
- GitHub artifact attestations or SLSA-style provenance for release artifacts.
- Least-privilege workflow permissions.
- Protected environments for production publication.

## Release automation target

Use automation to create evidence, not to bypass review:

1. Validate code, docs, schemas, and workflows.
2. Build/rebuild corpus artifacts deterministically.
3. Generate manifests and checksums.
4. Generate release evidence ledger.
5. Upload/update Hugging Face only after validation gates pass.
6. Create/update Zenodo drafts using or formally evaluating `zenodraft`.
7. Publish Zenodo only through protected approval.
8. Attach artifact attestations or provenance where supported.
9. Update changelog, release notes, CITATION, dataset cards, and DOI references consistently.

## Automation anti-patterns

- Do not publish to Zenodo in the same unprotected job that uploads draft files.
- Do not let dependency-update PRs publish to Hugging Face or Zenodo.
- Do not maintain disconnected version numbers in `VERSION`, `pyproject.toml`, release notes, and dataset cards without a sync check.
- Do not rely only on GitHub Releases for large data.
- Do not hide partial/review-stage status in generic version numbers.

## Track requirements

Each repo should maintain tracks for:

- versioning and release automation;
- CI/CD and code-quality hardening;
- documentation/metadata consistency checks;
- artifact provenance and attestations;
- dependency automation with Renovate;
- Rust-backed tooling adoption where feasible.
