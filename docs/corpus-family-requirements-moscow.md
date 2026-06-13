# Corpus Family Alignment Requirements

## Purpose

Define cross-repository requirements for aligning the New Zealand corpus family across `corpus-nz-legislation` and `corpus-nz-hansard`.

The local repository currently lives at `corpus-law-nz`, but the preferred systematic public label is `corpus-nz-legislation`. The sibling Hansard project is `corpus-nz-hansard`.

## Naming decision

Preferred project labels:

- Legislation corpus: `corpus-nz-legislation`.
- Hansard corpus: `corpus-nz-hansard`.

Agents working in either repository must treat these labels as the target naming convention for future public metadata, roadmaps, repository references, and environment planning. Existing published URLs may remain until a rename or migration track proves that redirects, citations, and DOI metadata are safe.

## MoSCoW Requirements

### Must

- Cross-reference `C:\Users\60217257\OneDrive - Flinders\repos\corpus-nz-hansard` in alignment work.
- Use `corpus-nz-legislation` as the preferred systematic name for future legislation repo and environment naming decisions.
- Keep existing published GitHub, Hugging Face, and Zenodo identifiers stable unless a migration plan preserves citations, redirects, and provenance.
- Align public metadata across GitHub, Hugging Face, Zenodo, OSF, and any future mirrors before declaring a release complete.
- Keep GitHub code-only: source, workflows, schemas, tests, docs, manifests, tiny fixtures, and release metadata only.
- Keep Hugging Face as the operational dataset surface for live or canonical Parquet data, with Xet-aware upload behaviour and explicit access/gating state.
- Keep Zenodo as the fixed DOI archival surface, with draft-first production workflows and protected publication approval.
- Treat OSF as optional review/mirror infrastructure only; do not add OSF as a required publication surface unless a future track establishes file-size, versioning, and maintenance policy.
- Ensure dataset cards, README files, citation files, release notes, and archive metadata make the same coverage and licensing claims.
- Include environment-specific verification tasks for GitHub, Hugging Face, Zenodo, OSF, and any additional public surfaces in release tracks.
- Preserve the full-coverage caveat until an authoritative work-ID inventory or documented reconciliation exists.

### Should

- Add a shared publication-surface audit checklist for GitHub, Hugging Face, Zenodo, OSF, and future mirrors.
- Align repository topics, descriptions, homepage URLs, release tags, licenses, CITATION metadata, and README badges across the corpus family.
- Publish Hugging Face datasets with viewer-friendly layouts that avoid manifest JSON files being interpreted as dataset splits when that breaks the viewer.
- Add Croissant, RO-Crate, Frictionless Data Package, DCAT, and PROV-O metadata as derived metadata artifacts once stable.
- Keep a sibling-project compatibility table showing shared fields, divergent fields, and release-surface differences.
- Use the legislation repository as the engineering baseline and the Hansard repository as the parliamentary-interoperability baseline.

### Could

- Reserve or migrate public GitHub repository names to `corpus-nz-legislation` and `corpus-nz-hansard` when citation risk is low.
- Add OSF review bundles for lightweight documentation/manifests or archive mirrors if the file-size policy is documented.
- Add a common Hugging Face organisation or collection for both corpora.
- Add a shared static documentation site that links both corpora and their current release states.
- Add dataset health badges for latest GitHub Actions, Hugging Face revision, Zenodo DOI, schema version, and coverage status.

### Won't

- Rename or delete published Zenodo records.
- Break existing Hugging Face or GitHub URLs without a documented redirect/migration plan.
- Treat OSF as a replacement for Hugging Face or Zenodo.
- Claim source-content relicensing where the project only licenses code, manifests, and documentation.
- Hide partial, review-stage, or derived-artifact status behind generic release language.

## SOTA Tooling Convergence Requirements

### Must

- **Ruff** with ALL applicable rule sets (49 codes — E, F, I, N, UP, B, SIM, A, ARG, C4, COM, DJ, DTZ, EM, ERA, EXE, FA, FLY, FURB, ICN, INP, INT, ISC, LOG, NPY, PD, PERF, PGH, PIE, PL, PLC, PLE, PLR, PLW, PT, PTH, PYI, Q, RET, RSE, RUF, S, SLF, T10, T20, TC, TID, TRY, W) enabled in strict mode, with `per-file-ignores` for `tests/*`, `tests/fixtures/*`, `scripts/*`, and `scripts/__init__.py`. Enforced in CI via `code_quality.yml` using `uv run ruff check .`.
- **`ty` static type checking** with `all = "error"` configured across `root = ["src", "tests", "scripts"]` and python-version `"3.11"`. Enforced in CI via `code_quality.yml` using `uv run ty check src tests scripts`.
- **`uv`** for frozen dependency installation (`uv sync --extra dev --frozen`) and task running (`uv run ...`) in both `code_quality.yml` and `tests.yml` workflows. The `astral-sh/setup-uv@v7` action bootstraps uv in CI.
- **`pytest`** as the primary test framework with distinct `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.smoke`, and `@pytest.mark.hypothesis` markers registered in `pyproject.toml` under `[tool.pytest.ini_options]`. Test paths rooted at `tests/` with `pythonpath = ["src"]`.
- **pydantic v2 with `pydantic-settings.BaseSettings`** for all environment-based configuration, replacing raw `@dataclass` + `os.getenv()` patterns. Both `pydantic>=2.0.0` and `pydantic-settings>=2.0.0` are declared as core dependencies.
- **Hypothesis property-based testing** for pure functions (`_parse_int_header`, `_retry_after_seconds`, `slug_for_path`, URL/content-type mappings). Already present in `tests/test_property_based.py`.
- **Coverage reporting** via `pytest-cov` with `fail_under = 60` in `[tool.coverage.report]`, `branch = true`, and XML output (`--cov-report=xml`) uploaded to Codecov in CI.
- **`ruff format --check`** enforced in CI alongside lint checks via a dedicated step in `code_quality.yml`.

### Should

- **Integration test directory** (`tests/integration/`) for cross-component pipeline tests (sync→validate→manifest→coverage, HF upload workflow). Already present with `tests/integration/test_sync_manifest_pipeline.py`.
- **Smoke test directory** (`tests/smoke/`) for full CLI pipeline tests via `typer.testing.CliRunner`. Already present with `tests/smoke/test_cli_smoke.py`.
- **Scalene profiling configuration** in `pyproject.toml` under `[tool.scalene]` (cpu, memory enabled; gpu, profile_all disabled; reduced_profile true) for performance-sensitive corpus bootstrap and upload paths.
- **Vale prose linter** configuration (`.vale.ini` exists at repository root) for documentation file quality.

### Could

- **`uv_build`** as the build backend (replacing hatchling) for unified uv toolchain.
- **Codecov CI upload** step for coverage trend tracking across branches. Already present in `tests.yml` with `fail_ci_if_error: false`.
- **Mutation testing** (e.g., `mutmut` or `cosmic-ray`) for critical validation and normalization paths.
- **Fuzz testing** for API response parsing paths using Hypothesis' `binary()` and `text()` strategies.

### Won't

- Remove existing test types or lower coverage thresholds without a documented plan and track.
- Add tools that duplicate existing coverage (e.g., pylint, mypy, black, isort alongside ruff).
- Mandate pydantic for internal data structures that are already served well by frozen dataclasses and typed dicts.
- Gate merges on Codecov CI status until the upload is proven stable across branch/PR workflows.

## Priority Order

1. Record naming preference and sibling-project cross-reference in both Conductor setups.
2. Create publication-surface alignment tracks in both repositories.
3. Audit GitHub/Hugging Face/Zenodo current state and document gaps. Current
   legislation evidence is recorded in `docs/public_surface_evidence_ledger.md`.
4. Decide whether to reserve or migrate `corpus-nz-legislation` public repository naming.
5. Fix Hugging Face viewer/access/metadata issues where present.
6. Align Zenodo related identifiers, licenses, archive files, and concept DOI references.
7. Decide OSF role and document file-size/mirror policy.
8. Add optional SOTA metadata packages: Croissant, RO-Crate, Frictionless, DCAT/PROV-O.
9. Converge on SOTA Python tooling: ruff strict, ty strict, pydantic v2 config, hypothesis property-based tests, integration/smoke test directories, and coverage baselines.

## Additional Implementation Recommendations

The following recommendations are part of the corpus-family roadmap and should be converted into implementation evidence before release polish is considered complete:

- Preserve the Track 24 naming/publication decision in
  `docs/naming_publication_alignment.md`.
- Keep the public-surface audit evidence ledger current for GitHub, Hugging
  Face, Zenodo, OSF, and future metadata environments:
  `docs/public_surface_evidence_ledger.md`.
- Add Zenodo rights/metadata harmonisation, including license-scope review for code, docs, manifests, source text, normalized Parquet, and archive bundles.
- Add a GitHub repository-name migration assessment before moving from `corpus-legislation-nz` toward `corpus-nz-legislation`.
- Add a shared NZ corpus core schema compatibility track covering `record_schema_version`, canonical `text`, timestamps, hashes, and provenance fields.
- Add generated SOTA metadata packages only through validated exporters: Croissant, RO-Crate, Frictionless Data Package, DCAT, and PROV-O.
- Add dataset-viewer and machine-consumability gates: dataset card parses, files are public if intended, Hugging Face viewer works or is intentionally disabled, DuckDB/PyArrow examples work, and manifest hashes are cited.
- Treat OSF as inactive until a standalone optional mirror policy is approved.
- Add SOTA tooling convergence evidence: ruff strict lint/format CI compliance, ty static type checking CI compliance, pydantic v2 BaseSettings migration completion, Hypothesis property-based test coverage, integration/smoke test directory proof, and coverage baseline stability.

## Zenodo tooling requirement

Future Zenodo draft/archive implementation work should use or formally evaluate `zenodraft` from `https://github.com/zenodraft/zenodraft`.

Required planning points:

- `zenodraft` is a Node/npm CLI for Zenodo and Zenodo Sandbox depositions.
- It supports creating concept/version drafts, adding/deleting files, validating/updating metadata, showing draft/prereserved DOI details, and publishing drafts.
- It supports sandbox operations with `--sandbox`.
- It expects `ZENODO_ACCESS_TOKEN` and/or `ZENODO_SANDBOX_ACCESS_TOKEN` rather than this repository's current `ZENODO_TOKEN` naming, so workflows must map secrets deliberately without printing values.
- Use `npx zenodraft ...` or a pinned npm install in CI; document Node/npm version requirements before adoption.
- Publication must remain draft-first and reviewer-approved; `zenodraft deposition publish` must be gated separately from upload/update steps.
