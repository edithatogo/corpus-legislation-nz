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

## Zenodo tooling requirement

Future Zenodo draft/archive implementation work should use or formally evaluate `zenodraft` from `https://github.com/zenodraft/zenodraft`.

Required planning points:

- `zenodraft` is a Node/npm CLI for Zenodo and Zenodo Sandbox depositions.
- It supports creating concept/version drafts, adding/deleting files, validating/updating metadata, showing draft/prereserved DOI details, and publishing drafts.
- It supports sandbox operations with `--sandbox`.
- It expects `ZENODO_ACCESS_TOKEN` and/or `ZENODO_SANDBOX_ACCESS_TOKEN` rather than this repository's current `ZENODO_TOKEN` naming, so workflows must map secrets deliberately without printing values.
- Use `npx zenodraft ...` or a pinned npm install in CI; document Node/npm version requirements before adoption.
- Publication must remain draft-first and reviewer-approved; `zenodraft deposition publish` must be gated separately from upload/update steps.
