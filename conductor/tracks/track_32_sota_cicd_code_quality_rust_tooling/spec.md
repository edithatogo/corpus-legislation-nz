# Spec - SOTA CI/CD Code Quality And Rust Tooling

## Status
todo

## Goal

Adopt SOTA CI/code-quality automation using Rust-backed tools where possible: `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, plus `actionlint`.

## Current State

The repository already has a strict local `ty` baseline in `pyproject.toml`; the remaining track work is to make the complete quality/security automation explicit, reproducible, and CI-backed without weakening publication gates.

## Acceptance Criteria

- Aligns with `docs/bleeding-edge-versioning-ci-quality.md`.
- Preserves `corpus-nz-legislation` and `corpus-nz-hansard` naming.
- Uses Rust-backed tooling where practical: `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, and local `ripgrep` guidance.
- Documents the local commands and CI commands for `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, and `actionlint`.
- Adds or verifies CodeQL, OpenSSF Scorecard, Renovate, and pre-commit policy as explicit adoption decisions.
- Keeps publication to Hugging Face and Zenodo behind validation gates.
- For Zenodo work, uses or formally evaluates `https://github.com/zenodraft/zenodraft`.
