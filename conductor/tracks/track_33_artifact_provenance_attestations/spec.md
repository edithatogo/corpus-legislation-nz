# Spec - Artifact Provenance And Attestations

## Status
todo

## Goal

Add release evidence ledgers, GitHub artifact attestations or SLSA-style provenance, and signed/checksummed artifact policy.

## Acceptance Criteria

- Aligns with `docs/bleeding-edge-versioning-ci-quality.md`.
- Preserves `corpus-nz-legislation` and `corpus-nz-hansard` naming.
- Uses Rust-backed tooling where practical: `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, and local `ripgrep` guidance.
- Defines a release evidence ledger covering commit SHA, workflow run, Hugging Face revision, Zenodo DOI/concept DOI where applicable, manifest hash, checksums, schema version, record count, and coverage statement.
- Adds an explicit decision on GitHub artifact attestations, SLSA-style provenance, or signed/checksummed artifacts for each release artifact class.
- Keeps publication to Hugging Face and Zenodo behind validation gates.
- For Zenodo work, uses or formally evaluates `https://github.com/zenodraft/zenodraft`.
