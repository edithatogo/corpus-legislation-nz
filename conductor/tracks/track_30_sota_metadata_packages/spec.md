# Spec - SOTA Metadata Packages

## Status
todo

## Goal

Generate validated Croissant, RO-Crate, Frictionless, DCAT, and PROV-O metadata packages.

## Acceptance Criteria

- The work preserves the preferred corpus-family labels corpus-nz-legislation and corpus-nz-hansard.
- GitHub, Hugging Face, Zenodo, OSF, and future metadata environments are considered where relevant.
- Croissant, RO-Crate, Frictionless, DCAT, and PROV-O outputs are generated from canonical manifests or metadata inputs rather than hand-edited as release artifacts.
- Each generated metadata package has validation commands, checksums, source-manifest references, and publication-surface links.
- Evidence is recorded in the track and linked documentation.
- Existing published URLs and DOI records are not broken without a migration plan.

## Zenodo Requirement

Any Zenodo draft/archive workflow work in this track must use or formally evaluate zenodraft from https://github.com/zenodraft/zenodraft. Publication commands must remain separate from draft upload/update commands and require protected approval.
