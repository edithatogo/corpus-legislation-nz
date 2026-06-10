# GitHub Repository Name Migration Assessment

Date: 2026-06-10.

This document records the Track 28 assessment for the preferred GitHub name
`corpus-nz-legislation`.

## Decision

Do not rename the live GitHub repository in this track.

Recommended path:

1. Reserve `edithatogo/corpus-nz-legislation` as a lightweight compatibility or
   redirect repository if the name remains available.
2. Keep the current live automation repository at
   `edithatogo/corpus-legislation-nz` until a migration window can update every
   dependent public surface in one controlled pass.
3. If a full rename is later approved, rename GitHub first, then immediately
   update repository variables, local remotes, documentation, dataset cards,
   Zenodo related identifiers, CI badges, release notes, and public-surface
   evidence.

Rationale: GitHub usually redirects renamed repositories, but repository names
are already embedded in release URLs, workflow evidence, branch-protection
evidence, Zenodo related identifiers, CITATION metadata, Hugging Face cards, and
Conductor status. A live rename should therefore be treated as a release
operation, not a routine cleanup.

## Current Evidence

Live source repository:

- Repository: `edithatogo/corpus-legislation-nz`.
- URL: `https://github.com/edithatogo/corpus-legislation-nz`.
- Visibility: public.
- Default branch: `main`.
- Latest release: `v0.1.0-partial.20260609`.
- Local remote: `https://github.com/edithatogo/corpus-legislation-nz.git`.
- Current local branch: `main`.

Preferred target name:

- Repository checked: `edithatogo/corpus-nz-legislation`.
- Current check result: not found or not accessible through `gh repo view`.

Sibling corpus:

- Preferred and current Hansard repository:
  `https://github.com/edithatogo/corpus-nz-hansard`.

## Migration Options

| Option | Description | Assessment |
| --- | --- | --- |
| Keep current repo only | Continue using `corpus-legislation-nz` publicly and `corpus-nz-legislation` as a family label in docs. | Lowest risk; keeps release and workflow evidence stable, but leaves naming asymmetry with Hansard. |
| Reserve preferred name | Create `edithatogo/corpus-nz-legislation` as a small pointer repository that links to the live repo, Hugging Face dataset, Zenodo DOI, and Hansard sibling. | Recommended next live action; protects the preferred name without breaking current URLs. |
| Rename live repo now | Rename `corpus-legislation-nz` to `corpus-nz-legislation`. | Technically possible but not recommended without a bundled migration PR and live post-rename checks. |
| Rename plus compatibility repo | Rename live repo, then recreate `corpus-legislation-nz` as a pointer repository if GitHub permits it after redirect setup. | Best final naming outcome but highest operational risk; needs a migration window and rollback notes. |

## Public Surface Implications

GitHub:

- Branch protection, required checks, releases, issues, PR links, workflow run
  links, environment rules, and repository variables must be rechecked after any
  rename.
- GitHub redirects should not be the only migration evidence; record the new
  canonical URL and verify old links.

Hugging Face:

- Live dataset remains `edithatogo/corpus-legislation-nz`.
- Historical dataset remains `edithatogo/corpus-legislation-nz-historical`.
- Do not rename Hugging Face again in the same operation unless the dataset
  cards, DOI-bound legacy shell, and redirect behavior are explicitly retested.

Zenodo:

- Published DOI record `10.5281/zenodo.20592540` remains immutable.
- Related identifiers may be updated if the GitHub repository becomes a related
  identifier in a future Zenodo version or metadata update.
- Existing archive file names must not be renamed.

OSF:

- OSF is inactive. No repository-name action is required unless a future mirror
  or review bundle is approved.

Future metadata:

- Croissant, RO-Crate, Frictionless, DCAT, and PROV-O outputs should use the
  preferred family label `corpus-nz-legislation` but include the current
  canonical publication URLs in their identifier fields until migration is
  complete.

## Pre-Rename Checklist

Before a full live rename:

1. Confirm no open issues or pull requests need stable URLs for review.
2. Confirm the preferred target name is still available or reserved by the
   maintainer.
3. Create a release/migration note that states the old and new URLs.
4. Record branch protection and workflow status before the rename.
5. Rename the GitHub repository.
6. Update local `origin` remote.
7. Re-run CI on the renamed repository.
8. Recheck branch protection, environments, variables, secrets by name, and
   workflow permissions.
9. Update README, DATASET_CARD, CITATION, public launch docs, public-surface
   ledger, Conductor docs, and future metadata package templates.
10. Verify old GitHub URLs redirect to the new repository.
11. Decide whether `corpus-legislation-nz` should remain a compatibility
    pointer repository after the redirect period.

## Reservation Repository Contract

If `edithatogo/corpus-nz-legislation` is reserved before a full migration, it
should be code-light and contain only:

- A README stating that the live repository is
  `https://github.com/edithatogo/corpus-legislation-nz`.
- Links to the Hugging Face live and historical datasets.
- Link to Zenodo record `10.5281/zenodo.20592540`.
- Link to sibling `https://github.com/edithatogo/corpus-nz-hansard`.
- A statement that full migration is pending and no data should be uploaded
  there.

Do not duplicate workflows, secrets, branch protection, issues, or generated
data into the reservation repository.
