# Naming and publication alignment

Last updated: 2026-06-10.

This document records the Track 24 naming/publication decision for the
legislation corpus and its sibling Hansard corpus.

## Decision

Preferred corpus-family labels:

- Legislation: `corpus-nz-legislation`.
- Hansard: `corpus-nz-hansard`.

Current published legislation surfaces intentionally remain on the
`corpus-legislation-nz` naming line:

- GitHub: `https://github.com/edithatogo/corpus-legislation-nz`.
- Hugging Face live dataset:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Hugging Face historical dataset:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical`.
- Zenodo DOI snapshot: `https://zenodo.org/records/20592540`.

Do not rename published surfaces again in this track. Migration or reservation
of `corpus-nz-legislation` is assessed in Track 28 so release links, redirects,
DOI metadata, Hugging Face legacy shells, and citation instructions can be
reviewed together. The Track 28 assessment recommends reserving
`edithatogo/corpus-nz-legislation` as a pointer repository before any live
rename of the current automation repository.

## Sibling corpus

Sibling project:

- Local path:
  `C:\Users\60217257\OneDrive - Flinders\repos\corpus-nz-hansard`.
- GitHub remote:
  `https://github.com/edithatogo/corpus-nz-hansard.git`.

The Hansard repository is the parliamentary-interoperability reference for
future derived artifacts and metadata endpoints. This legislation repository is
the API-first legislation baseline for publication, release evidence, and
provenance-safe archiving.

## Current publication alignment

| Environment | Current legislation surface | Track 24 decision |
| --- | --- | --- |
| GitHub | `edithatogo/corpus-legislation-nz` | Keep stable; Track 28 assesses reservation/migration to `corpus-nz-legislation`. |
| Hugging Face live | `edithatogo/corpus-legislation-nz` | Keep stable; do not overwrite with historical records. |
| Hugging Face historical | `edithatogo/corpus-legislation-nz-historical` | Keep separate from the live dataset. |
| Hugging Face legacy | `edithatogo/nz-legislation-corpus` | Keep as DOI-bound compatibility shell pointing to the renamed live dataset. |
| Zenodo | `10.5281/zenodo.20592540` | Keep immutable; related identifier points to the renamed HF live dataset. |
| OSF | inactive | Optional only after a mirror/review policy exists. |
| Future metadata | inactive | Croissant, RO-Crate, Frictionless, DCAT, and PROV-O remain generated roadmap artifacts. |

Current public-surface evidence is in
`docs/public_surface_evidence_ledger.md`.

## Metadata alignment requirements

Public metadata should consistently express:

- preferred family label `corpus-nz-legislation`;
- current published label `corpus-legislation-nz`;
- sibling label `corpus-nz-hansard`;
- partial/API-discovery coverage caveat for the live dataset;
- historical bootstrap caveat for the historical dataset;
- code/data/source-rights separation;
- Zenodo DOI as fixed-version citation and Hugging Face as live operational
  dataset surface.

## Immediate gaps and follow-up tracks

- GitHub topics and homepage are empty at the Track 24 evidence point. Add
  topics/homepage only after deciding the stable public documentation URL.
- Dataset cards can include richer sibling/family links after Track 25 defines
  cross-corpus interoperability expectations.
- Migration/reservation of `corpus-nz-legislation` is Track 28, not Track 24.
- Track 28 assessment:
  `docs/github_repository_name_migration_assessment.md`.
- Rights metadata and future `zenodraft` evaluation are Track 27.
- Shared schema and generated metadata packages are Tracks 29 and 30.

## Guardrails

- Do not delete or rename published Zenodo records.
- Do not break GitHub or Hugging Face URLs without a redirect/citation plan.
- Do not claim full legislation coverage until Track 04 is closed.
- Do not treat OSF as a required publication surface unless a future policy
  approves it.
- Do not hand-edit future metadata packages; generate them from manifests and
  validated source metadata.
