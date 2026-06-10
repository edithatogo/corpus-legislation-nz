# Plan - SOTA CI/CD Code Quality And Rust Tooling

## Tasks

- [ ] Define current state and target state.
- [ ] Record the existing strict `ty` baseline and the exact local validation commands that must stay green.
- [ ] Add/update CI checks with least-privilege permissions.
- [ ] Add/update local commands or Makefile targets.
- [ ] Add documentation consistency and release evidence checks.
- [ ] Add Renovate/package update policy where applicable.
- [ ] Decide and document pre-commit adoption scope.
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
