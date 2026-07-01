# Plan - Period-Sharded Bootstrap Agent Handoff

## Tasks

- [x] Review the API-native/recent annual-shard boundary from repo evidence and
  record that no authoritative boundary is currently verified; the manifest
  must carry 2008 only as an unverified planning fallback.
- [x] Define the canonical period policy and record why recent years should be
  annual rather than coarse multi-year periods.
- [x] Add a generator that reads `seeds/work_ids.txt` plus available source
  metadata and writes period seed files plus a period manifest.
- [x] Ensure the generator proves each work ID is assigned to exactly one
  period or an explicit unknown-year review shard.
- [x] Add tests for period assignment, manifest hashing, annual recent shards,
  and unknown-year handling.
- [x] Extend the full-corpus workflow or add a companion workflow that runs by
  period and uploads a checkpoint artifact immediately after each period
  completes.
- [x] Extend `nzlc review-full-corpus-bootstrap` or add a companion command so
  a single period artifact can be reviewed as a standalone handoff unit.
- [x] Add a Conductor handoff table listing period, status, artifact, reviewer,
  failed-version count, manifest hash, and next action.
- [x] Document that Track 07's current serial all-batch run is valid evidence
  for the full bootstrap, but it is not the final period-handoff workflow.
- [ ] After implementation, create period-specific follow-up tracks only for
  periods that have completed artifacts and need independent agent review.

## Initial Period Recommendation

Use coarse historical periods and annual recent periods:

- `pre_1908`
- `1908_1949`
- `1950_1979`
- `1980_1999`
- `2000_api_boundary_minus_1`
- annual shards from the verified API-native/recent boundary through the
  current year
- `unknown_year_review` for work IDs whose year cannot be derived

Rationale: older periods can be reviewed as larger blocks because the work is
mostly historical completeness, fallback, and source-quality triage. Recent
years should be annual once the corpus reaches API-native coverage because they
are more likely to support recurring maintenance, public release notes,
downstream research slices, and faster agent handoff.

## Current Evidence

- Existing deterministic batches are 68 chunks of 500 work IDs.
- The early reviewed batches are broadly chronological:
  - batch 0001: `act_imperial_1539_1` through `act_local_1889_22`
  - batch 0002: `act_local_1889_23` through `act_local_1908_30`
  - batch 0003: `act_local_1908_31` through `act_local_1934_10`
  - batch 0004: `act_local_1934_11` through `act_local_1968_8`
  - batch 0005: `act_local_1969_1` through `act_private_1946_1`
- Existing batches are operational chunks, not formal period handoff units.
- The current Track 07 run `27898963687` is an all-batch serial run; it can
  validate the full bootstrap but cannot produce immediate per-period agent
  handoff artifacts unless the workflow is extended or rerun by period.
- Implemented `src/nz_legislation_corpus/period_shards.py` with canonical
  period assignment, metadata-based year derivation from `work_id`,
  `latest_version_id`, then `title`, manifest generation, assignment proof, and
  unknown-year routing.
- Period manifests now include `api_boundary_decision`, which records boundary
  year, source, verification status, annual-shard start year, and a warning when
  the boundary is only the conservative 2008 planning fallback.
- Added CLI command:
  `nzlc split-work-id-periods`.
- Added companion workflow:
  `.github/workflows/full_corpus_period_bootstrap.yml`.
- Extended `nzlc review-full-corpus-bootstrap` to include
  `generated/full-corpus-periods/period_context.json` when present in a period
  checkpoint artifact.
- Review fix: period checkpoint context now carries `api_boundary_decision`, and
  `nzlc review-full-corpus-bootstrap` reads `work_id_count` from the workflow's
  nested `period` context so period handoff reports do not lose source work-ID
  counts.
- Focused tests passed:
  `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_period_shards.py tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py -q`
  reported 26 passed.
- Ruff passed:
  `.venv\Scripts\python.exe -m ruff check --no-cache src\nz_legislation_corpus\period_shards.py src\nz_legislation_corpus\bootstrap_review.py src\nz_legislation_corpus\cli.py tests\test_period_shards.py tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py`.
- Workflow lint passed:
  `actionlint .github\workflows\full_corpus_period_bootstrap.yml`.

## Handoff Table

| Period | Status | Artifact | Reviewer | Failed versions | Manifest hash | Next action |
| --- | --- | --- | --- | ---: | --- | --- |
| `pre_1908` | pending checkpoint | pending | unassigned | unknown | pending | Run period workflow after boundary policy review. |
| `1908_1949` | pending checkpoint | pending | unassigned | unknown | pending | Run period workflow after boundary policy review. |
| `1950_1979` | pending checkpoint | pending | unassigned | unknown | pending | Run period workflow after boundary policy review. |
| `1980_1999` | pending checkpoint | pending | unassigned | unknown | pending | Run period workflow after boundary policy review. |
| `2000_2007` | pending checkpoint | pending | unassigned | unknown | pending | Generated when using the unverified 2008 fallback boundary. |
| `year_2008+` | pending checkpoint | pending | unassigned | unknown | pending | Annual shards are allowed for handoff planning, but the manifest warning blocks API-native boundary claims until verified. |
| `unknown_year_review` | pending manifest generation | pending | unassigned | unknown | pending | Review after `split-work-id-periods` identifies unknown-year work IDs. |

## Open Questions

- What is the verified API-native/recent boundary year? Current repo-side
  answer: not verified; use 2008 only as a planning fallback recorded in the
  manifest.
- Should the annual recent period begin at the official API coverage boundary,
  the earliest year with reliable source metadata, or a project-chosen
  maintenance boundary?
- Should unknown-year works block a period, or be reviewed in a separate
  `unknown_year_review` shard before final completeness claims?
