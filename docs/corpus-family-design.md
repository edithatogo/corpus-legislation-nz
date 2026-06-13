# Corpus Family Alignment Design

## Design Principle

`corpus-nz-legislation` and `corpus-nz-hansard` should operate as sibling projects in a systematic New Zealand public-text corpus family. They may have different source systems and schemas, but they should share naming conventions, publication-surface rules, validation gates, and release evidence patterns.

## Preferred Names

| Corpus | Preferred project label | Current/local or published names observed | Naming action |
| --- | --- | --- | --- |
| Legislation | `corpus-nz-legislation` | local `corpus-law-nz`; GitHub `corpus-legislation-nz`; package `corpus-legislation-nz` | Track migration/reservation without breaking citations. |
| Hansard | `corpus-nz-hansard` | local/GitHub `corpus-nz-hansard`; HF `nz-hansard-corpus` | Keep, and align metadata references. |

## Publication Surface Model

```mermaid
flowchart LR
  subgraph Family["NZ corpus family"]
    L["corpus-nz-legislation"]
    H["corpus-nz-hansard"]
  end
  subgraph GitHub["GitHub: code and automation"]
    LGH["legislation repo / workflows / releases"]
    HGH["hansard repo / workflows / releases"]
  end
  subgraph HF["Hugging Face: operational datasets"]
    LHF["edithatogo/corpus-legislation-nz"]
    HHF["edithatogo/nz-hansard-corpus"]
  end
  subgraph Zenodo["Zenodo: fixed DOI archives"]
    LZ["10.5281/zenodo.20592540"]
    HZ["10.5281/zenodo.20595194"]
  end
  subgraph Optional["Optional mirrors and metadata"]
    OSF["OSF review/mirror bundles"]
    META["Croissant / RO-Crate / Frictionless / DCAT / PROV-O"]
  end
  L --> LGH --> LHF --> LZ
  H --> HGH --> HHF --> HZ
  LGH -.cross-reference.-> HGH
  LHF -.dataset family links.-> HHF
  LZ -.related identifiers.-> HZ
  LGH --> OSF
  HGH --> OSF
  LHF --> META
  HHF --> META
```

## Environment Alignment Matrix

| Environment | Shared role | Legislation requirement | Hansard requirement |
| --- | --- | --- | --- |
| GitHub | Code, tests, CI, releases, docs, lightweight packages | Prefer future label `corpus-nz-legislation`; keep current published repo stable until migration plan. | Continue `corpus-nz-hansard`; add engineering alignment with legislation baseline. |
| Hugging Face | Dataset hosting, Parquet, cards, Xet storage | Keep `edithatogo/corpus-legislation-nz`; verify access/gating and viewer layout. | Keep `edithatogo/nz-hansard-corpus`; fix viewer split/layout issue and verify ungated access. |
| Zenodo | Fixed DOI archives | Keep published DOI; align related identifiers to GitHub and HF; license must not overclaim source rights. | Keep latest DOI; mark older review DOI as superseded; align license/source-rights wording. |
| OSF | Optional review or mirror | Do not require until file-size/splitting and citation policy are documented. | Same; use only for review bundles or mirrors if explicitly approved. |
| Future metadata registries | SOTA discovery and interoperability | Add Croissant/RO-Crate/Frictionless/DCAT/PROV-O as generated metadata artifacts. | Same; can use Hansard interoperability tracks as baseline. |

## Release Gate Diagram

```mermaid
flowchart TD
  A["Prepare release candidate"] --> B["GitHub metadata and CI audit"]
  B --> C["Hugging Face dataset card, files, access, viewer audit"]
  C --> D["Zenodo draft metadata, files, related identifiers audit"]
  D --> E["Optional OSF/mirror decision"]
  E --> F["Cross-corpus naming and sibling-link audit"]
  F --> G{"All public claims aligned?"}
  G -- No --> H["Fix docs/cards/metadata before release"]
  H --> B
  G -- Yes --> I["Approve publish or tag"]
  I --> J["Record evidence in Conductor track"]
```

Current legislation public-surface evidence is recorded in
`docs/public_surface_evidence_ledger.md`.

Track 24's naming/publication decision is recorded in
`docs/naming_publication_alignment.md`.

Track 25's Hansard interoperability mapping is recorded in
`docs/cross_corpus_interoperability_hansard.md`. It adopts reusable Hansard
patterns for DuckDB/search/RAG, endpoint contracts, linked data, generated
metadata packages, validation manifests, and optional publication surfaces while
keeping Hansard-specific parliamentary proceedings fields out of the legislation
core schema.

## CI/CD Pipeline Architecture

```mermaid
flowchart LR
    subgraph Push["Push / PR"]
        TEST_WF["tests.yml: pytest + coverage"]
        QUAL_WF["code_quality.yml: ruff check + format + ty + typos + taplo + actionlint + zizmor"]
        CODEQL["codeql.yml: CodeQL analysis"]
        SCORECARD["scorecard.yml: OpenSSF Scorecard"]
    end
    subgraph Schedule["Scheduled"]
        HF_SYNC["hf_sync.yml: daily live sync"]
        DOCTOR["doctor.yml: weekly health check"]
        MONTHLY["monthly_full_reconciliation.yml"]
    end
    subgraph Manual["Manual Dispatch"]
        BOOTSTRAP["full_corpus_bootstrap.yml"]
        HF_UPLOAD["full_corpus_hf_upload.yml"]
        HISTORICAL["historical_hf_upload.yml"]
        ZENODO["annual_zenodo_archive.yml"]
    end
    Push --> TEST_WF & QUAL_WF & CODEQL
    Schedule --> HF_SYNC & DOCTOR
    Manual --> BOOTSTRAP & HF_UPLOAD & HISTORICAL & ZENODO
```

Push and PR workflows run on every commit. Scheduled workflows run daily, weekly, or monthly without human intervention. Manual workflows are triggered through `workflow_dispatch` and typically require explicit confirmation flags (`upload_confirmed`, `publish`) before they mutate any publication surface. All workflows use `permissions: contents: read` unless they need specific tokens (Hugging Face, Zenodo) scoped to their job.

## Test Strategy

```mermaid
flowchart TD
    subgraph E2E["End-to-End (manual)"]
        E2E1["Trigger full_corpus_bootstrap.yml"]
        E2E2["Verify Hugging Face dataset"]
        E2E3["Verify Zenodo archive"]
    end
    subgraph Smoke["Smoke (tests/smoke/)"]
        S1["nzlc smoke-fixture -> validate -> manifest -> coverage-report"]
        S2["nzlc doctor (no network)"]
    end
    subgraph Integration["Integration (tests/integration/)"]
        I1["Sync -> validate -> manifest -> coverage pipeline"]
        I2["HF upload workflow with mocked API"]
    end
    subgraph Property["Property-Based (tests/)"]
        P1["Hypothesis: slug_for_path"]
        P2["Hypothesis: _parse_int_header"]
        P3["Hypothesis: _retry_after_seconds"]
    end
    subgraph Unit["Unit (tests/)"]
        U1["API client with FakeSession"]
        U2["Validation with sample fixtures"]
        U3["Manifest building with tmp_path"]
        U4["Download format fallback"]
        U5["Rate limit handling"]
        U6["HF sync prune/upload"]
        U7["Coverage report generation"]
        U8["RSS feed generation"]
    end
    E2E --> Smoke --> Integration --> Property --> Unit
```

Unit tests cover individual modules with isolated fixtures and fast assertions. Property-based tests use Hypothesis to find edge cases in string/header parsing. Integration tests exercise multi-step pipelines (sync → validate → manifest → coverage-report) against the real API in CI. Smoke tests run without secrets or network (offline doctor, fixture-based corpus). End-to-end tests are manual workflows that validate the full publication surface after a bootstrap or archive.

## Development Tooling Stack

```mermaid
flowchart LR
    subgraph Language["Python 3.11+"]
        PY311["uv_build build backend"]
    end
    subgraph Quality["Code Quality"]
        RUFF["ruff check (49 rule sets)"]
        RUFF_FMT["ruff format --check"]
        TY["ty check (all = error)"]
        TYPOS["typos spell checker"]
        TAPLO["taplo fmt --check pyproject.toml"]
    end
    subgraph Security["Security"]
        ZIZMOR["zizmor workflow audit"]
        CODEQL["CodeQL analysis"]
        SCORECARD["OpenSSF Scorecard"]
        ACTIONLINT["actionlint"]
    end
    subgraph Test["Testing"]
        PYTEST["pytest (unit/integration/smoke/hypothesis)"]
        COV["pytest-cov (coverage)"]
        HYP["hypothesis (property-based)"]
    end
    subgraph Config["Configuration"]
        PYDANTIC["pydantic v2 BaseSettings"]
    end
    subgraph Lint["Prose Linting"]
        VALE["vale prose linter"]
    end
    subgraph Profile["Profiling"]
        SCALENE["scalene profiler"]
    end
    Language --> Quality --> Security
    Language --> Test
    Language --> Config
    Quality --> Lint
    Test --> Profile
```

The Python toolchain uses `uv` for dependency management with a frozen lockfile in CI. `ruff` enforces 49 rule sets as a single blocking linter and formatter. `ty` runs strict type checking across `src`, `tests`, and `scripts`. `zizmor` audits workflow security (advisory until the hardening backlog is complete). `actionlint` checks workflow syntax. `pydantic` v2 `BaseSettings` governs all configuration through environment variables and `.env` files. `vale` provides prose linting for documentation. `scalene` is available for CPU/memory profiling during development.

## Design Notes

- GitHub is the automation and documentation controller, not the large-data host.
- Hugging Face is the browsable/operational dataset host and should remain ungated unless a deliberate access policy says otherwise.
- Zenodo records should be immutable citation snapshots and should link both GitHub and Hugging Face where possible.
- OSF is useful only if it adds review, institutional, or redundancy value without creating another unsynchronised source of truth.
- Every public surface should expose the same preferred naming family and sibling-corpus links.
- Derived interoperability artifacts should be generated, versioned, validated,
  checksummed, and optional. They must not expand the base runtime dependency
  set or replace dataset-specific core schemas without a separate implementation
  track.

## Recommended Additional Tracks

```mermaid
flowchart TD
    A["Corpus-family publication alignment"] --> B["Public-surface audit evidence"]
    A --> C["Zenodo rights metadata harmonisation"]
    C --> ZD["Zenodraft-based draft workflow"]
    A --> D["Shared NZ corpus core schema"]
    A --> E["SOTA metadata packages"]
    A --> F["OSF optional mirror policy"]
    A --> G["Dataset viewer and machine-consumability gates"]
    A --> T["SOTA tooling convergence"]
    T --> T1["Ruff strict (49 rule sets)"]
    T --> T2["Pyright/ty strict type checking"]
    T --> T3["Pydantic v2 configuration"]
    T --> T4["Hypothesis property-based tests"]
    T --> T5["Integration and smoke test directories"]
    T --> T6["Coverage baselines and CI reporting"]
    B --> H["Release evidence ledger"]
    D --> H
    E --> H
    G --> H
```

### Zenodraft integration design

Future Zenodo automation should prefer `zenodraft` (`https://github.com/zenodraft/zenodraft`) for draft deposition operations. The design target is:

1. Generate archive files and `.zenodo.json` metadata locally.
2. Run `zenodraft metadata validate .zenodo.json` before upload.
3. Use `zenodraft deposition create concept` or `zenodraft deposition create version <concept_id>` for draft creation.
4. Use `zenodraft file add` and `zenodraft metadata update` for draft contents.
5. Use `zenodraft deposition show prereserved` and `show details` to capture evidence.
6. Keep `zenodraft deposition publish` in a separate protected approval step.

CI must map repository secrets to `ZENODO_ACCESS_TOKEN` or `ZENODO_SANDBOX_ACCESS_TOKEN` only for the step that needs them.

Track 27's rights and zenodraft evaluation decision is recorded in
`docs/zenodo_rights_metadata_zenodraft.md`.

Track 28's GitHub repository-name migration assessment is recorded in
`docs/github_repository_name_migration_assessment.md`. It recommends reserving
`edithatogo/corpus-nz-legislation` as a pointer repository before any full live
rename of `edithatogo/corpus-legislation-nz`.

Track 29's shared core schema is recorded in
`docs/shared_nz_corpus_core_schema.md` and
`schemas/shared_nz_corpus_core.schema.json`.

Track 30's generated metadata package contract is recorded in
`docs/sota_metadata_packages.md`.
