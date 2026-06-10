# Plan - Bleeding Edge Versioning And Release Automation

## Tasks

- [ ] Define current state and target state.
- [ ] Define the authoritative version sources for code/package, dataset, schema, Hugging Face revision, Zenodo DOI snapshot, and manifest hash.
- [ ] Add consistency checks across `pyproject.toml`, release notes, `CITATION.cff`, dataset card text, manifests, and publication metadata.
- [ ] Decide whether to use Release Please or an equivalent Conventional Commits release-note/tag workflow.
- [ ] Add/update CI checks with least-privilege permissions.
- [ ] Add/update local commands or Makefile targets.
- [ ] Add documentation consistency and release evidence checks.
- [ ] Add Renovate/package update policy where applicable.
- [ ] Ensure dependency-update PRs cannot publish datasets or Zenodo records.
- [ ] Record validation evidence.

## Tooling Checklist

- [ ] `uv` frozen install/lock checks.
- [ ] `ruff check` and `ruff format --check`.
- [ ] `ty check` with strict rules for packaged modules.
- [ ] `typos` spelling/identifier check.
- [ ] `zizmor` workflow security audit.
- [ ] `taplo` TOML formatting/linting where TOML config exists.
- [ ] `actionlint` workflow syntax check.
- [ ] CodeQL and OpenSSF Scorecard.
- [ ] Artifact attestations or SLSA-style provenance for release artifacts.

## Verification

- [ ] Metadata JSON parses.
- [ ] Track is registered in `conductor/tracks.md`.
- [ ] All added checks are documented before enforcement.
