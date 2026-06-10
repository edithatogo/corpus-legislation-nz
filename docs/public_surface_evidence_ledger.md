# Public surface evidence ledger

Last reconciled: 2026-06-10.

This ledger records the current public surfaces for the legislation corpus after
the approved partial/API-discovery launch and the rename to
`corpus-legislation-nz`. It is evidence for Track 26 and should be refreshed
before any release, DOI update, repository rename, or full-coverage claim.

## Summary

| Surface | Current state | Evidence |
| --- | --- | --- |
| GitHub source repository | Public, code-only automation repository | `https://github.com/edithatogo/corpus-legislation-nz` |
| GitHub release/tag | Partial/API-discovery launch release exists | `v0.1.0-partial.20260609` |
| Hugging Face live dataset | Public, intentionally partial/API-discovery dataset | `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz` |
| Hugging Face historical dataset | Public historical bootstrap target, separate from live dataset | `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical` |
| Zenodo DOI snapshot | Published 2026 annual snapshot | `https://zenodo.org/records/20592540` |
| OSF | Not active | Optional only; no OSF mirror/review bundle has been approved. |
| Future metadata packages | Generator ready; not published | `docs/sota_metadata_packages.md` |

## Refresh evidence - 2026-06-10

This Track 26 implementation pass refreshed the public-surface evidence with
live GitHub, Hugging Face, and Zenodo probes. No public-surface drift requiring
a policy or documentation change was found.

Confirmed current evidence:

- GitHub repository remains public at
  `https://github.com/edithatogo/corpus-legislation-nz`.
- Latest GitHub release remains `v0.1.0-partial.20260609`.
- Open GitHub issues: `0`.
- Open GitHub pull requests: `0`.
- `main` branch protection still requires one approving review, strict `tests`,
  admin enforcement, linear history, no force pushes, and no deletions.
- GitHub variables still include
  `HF_REPO_ID=edithatogo/corpus-legislation-nz` and
  `HF_HISTORICAL_REPO_ID=edithatogo/corpus-legislation-nz-historical`.
- GitHub secrets still exist by name: `HF_TOKEN`,
  `NZ_LEGISLATION_API_KEY`, and `ZENODO_TOKEN`.
- Live Hugging Face dataset revision remains
  `6b082e2f85802cb374898d689d264017a047799b` with 19 files.
- Historical Hugging Face dataset revision remains
  `901a2ecc03e260758dc72bf965607a74a7417221` with 4644 files.
- Legacy DOI-bound Hugging Face dataset remains public at
  `edithatogo/nz-legislation-corpus` with revision
  `4487e26b19b4c3e130030cd333247233a42252d3`.
- `edithatogo/nz-legislation-corpus-historical` still resolves to canonical
  dataset ID `edithatogo/corpus-legislation-nz-historical`.
- Zenodo record `20592540` remains published/done, open access, dataset,
  license `cc-by-4.0`, revision `4`, and related to
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Zenodo rights-scope and future `zenodraft` migration policy are recorded in
  `docs/zenodo_rights_metadata_zenodraft.md`.
- GitHub repository-name migration assessment is recorded in
  `docs/github_repository_name_migration_assessment.md`; the preferred target
  `edithatogo/corpus-nz-legislation` was not found or not accessible at the
  Track 28 check point.

## GitHub

Evidence command:

```powershell
gh repo view edithatogo/corpus-legislation-nz --json nameWithOwner,url,defaultBranchRef,isPrivate,visibility,description,pushedAt,latestRelease
gh api repos/edithatogo/corpus-legislation-nz/branches/main/protection
gh variable list --repo edithatogo/corpus-legislation-nz
gh secret list --repo edithatogo/corpus-legislation-nz
gh run list --repo edithatogo/corpus-legislation-nz --limit 10
```

Observed state:

- Repository: `edithatogo/corpus-legislation-nz`.
- URL: `https://github.com/edithatogo/corpus-legislation-nz`.
- Visibility: public.
- Default branch: `main`.
- Description: `API-first NZ legislation corpus pipeline: NZ API -> optimized Parquet -> Hugging Face/Xet -> annual Zenodo DOI snapshots.`
- License reported by GitHub API: `MIT`.
- Latest release: `v0.1.0-partial.20260609`,
  `https://github.com/edithatogo/corpus-legislation-nz/releases/tag/v0.1.0-partial.20260609`.
- Open issues: none at reconciliation time.
- Open pull requests: none at reconciliation time.
- Repository topics: none at reconciliation time.
- Homepage: none at reconciliation time.

Branch protection on `main`:

- Required approving reviews: `1`.
- Required status checks: `tests`.
- Strict status checks: `true`.
- Admin enforcement: `true`.
- Linear history: `true`.
- Force pushes: disabled.
- Deletions: disabled.

Repository variables observed by name/value where non-secret:

- `HF_REPO_ID=edithatogo/corpus-legislation-nz`.
- `HF_HISTORICAL_REPO_ID=edithatogo/corpus-legislation-nz-historical`.
- `DATA_DIR=data`.
- `NZLC_SEARCH_TERMS=act,bill,regulation,order,notice`.
- `NZLC_SEARCH_FIELD=title`.
- `NZLC_SEARCH_SORT_BY=most_recently_updated`.
- `NZLC_LEGISLATION_TYPES=act,bill,secondary_legislation,amendment_paper`.
- `ARCHIVE_TITLE=New Zealand Legislation Corpus`.
- `ARCHIVE_LICENSE=cc-by-4.0`.
- `ARCHIVE_PUBLISH=false`.
- `ZENODO_API_URL=https://zenodo.org/api`.
- `ZENODO_SANDBOX_API_URL=https://sandbox.zenodo.org/api`.
- `ARCHIVE_CREATORS_JSON` exists; value is not repeated outside the GitHub
  variable inventory.

Repository secrets observed by name only:

- `HF_TOKEN`.
- `NZ_LEGISLATION_API_KEY`.
- `ZENODO_TOKEN`.

Recent workflow evidence:

- `Tests` passed on push for PR #47 merge:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27266470533`.
- `CodeQL` passed on push for PR #47 merge:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27266470497`.
- `OpenSSF Scorecard` passed after branch-protection update:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27266475605`.
- Temporary `Rename Hugging Face datasets` workflow passed:
  `https://github.com/edithatogo/corpus-legislation-nz/actions/runs/27265785491`.

## Hugging Face

Evidence command:

```powershell
uv run python -c "from huggingface_hub import HfApi; api=HfApi(); ..."
```

Observed live dataset:

- Dataset: `edithatogo/corpus-legislation-nz`.
- URL: `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Visibility: public.
- Current revision: `6b082e2f85802cb374898d689d264017a047799b`.
- File count reported by Hub API: `19`.
- Tags include: `language:en`, `license:other`, `format:json`,
  `library:datasets`, `library:pandas`, `library:polars`,
  `library:mlcroissant`, `new-zealand`, `legislation`, `law`,
  `legal-corpus`, `parquet`, `xet`.
- Scope: intentionally partial/API-discovery. Full New Zealand legislation
  coverage is not proven.

Observed historical dataset:

- Dataset: `edithatogo/corpus-legislation-nz-historical`.
- URL:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical`.
- Visibility: public.
- Current revision: `901a2ecc03e260758dc72bf965607a74a7417221`.
- File count reported by Hub API: `4644`.
- Tags include: `historical`, `parquet`, `new-zealand`, `legislation`, `law`,
  `legal-corpus`.
- Scope: successful historical bootstrap, not complete historical corpus
  coverage.

Legacy Hugging Face names:

- `edithatogo/nz-legislation-corpus` still exists as a public DOI-bound legacy
  dataset shell with revision `4487e26b19b4c3e130030cd333247233a42252d3`.
  Hugging Face did not allow moving this dataset after DOI generation. It is a
  compatibility surface and should point users to
  `edithatogo/corpus-legislation-nz`.
- `edithatogo/nz-legislation-corpus-historical` resolves to canonical dataset
  ID `edithatogo/corpus-legislation-nz-historical`.

## Zenodo

Evidence command:

```powershell
Invoke-RestMethod -Uri https://zenodo.org/api/records/20592540
```

Observed record:

- Record: `https://zenodo.org/records/20592540`.
- DOI: `10.5281/zenodo.20592540`.
- Concept DOI: `10.5281/zenodo.20592539`.
- Title: `New Zealand Legislation Corpus: 2026 annual snapshot`.
- Publication date: `2026-06-08`.
- Status/state: published / done.
- Access right: open.
- Resource type: dataset.
- License: `cc-by-4.0`.
- Version: `2026`.
- Creator: `edithatogo`.
- Record revision: `4`.
- Related identifier:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`
  with relation `isSupplementTo`.

Published files:

- `nz-legislation-corpus-2026.SHA256SUMS.txt`.
- `nz-legislation-corpus-2026.tar.zst`.
- `nz-legislation-corpus-2026.manifest.json`.

Immutable caveat:

- The Zenodo metadata related identifier has been updated to the renamed
  Hugging Face dataset.
- Published file names still contain the old `nz-legislation-corpus` prefix
  because the files are part of an immutable DOI snapshot. Do not rename or
  replace these files without creating a new Zenodo version through the protected
  annual archive path.

## OSF

OSF is inactive for this repository at reconciliation time.

Current policy:

- OSF is optional review or mirror infrastructure only.
- Do not add OSF as a required publication surface until a future track defines
  file-size, splitting, citation, checksum, update, and maintenance policy.
- OSF must not become a second unsynchronised source of truth.

## Future metadata surfaces

The following metadata packages are generated locally through validated
exporters, but are not yet active public outputs:

- Croissant.
- RO-Crate.
- Frictionless Data Package.
- DCAT.
- PROV-O.

Future metadata packages must cite the relevant source manifest hash, Hugging
Face revision, Zenodo DOI or draft identifier, schema version, and coverage
boundary.

Generator and validation commands:

```powershell
uv run nzlc metadata-packages --output-dir generated/metadata-packages
uv run nzlc validate-metadata-packages --metadata-dir generated/metadata-packages
```

## Naming and migration constraints

Preferred corpus-family labels remain:

- Legislation: `corpus-nz-legislation`.
- Hansard: `corpus-nz-hansard`.

Current legislation public surfaces intentionally use `corpus-legislation-nz`.
Do not rename GitHub, Hugging Face, or DOI-linked surfaces again without a
dedicated migration/reservation assessment that protects:

- GitHub release links and branch protection.
- Hugging Face dataset redirects and DOI-bound legacy shells.
- Zenodo related identifiers and immutable file names.
- Citation instructions in `CITATION.cff`, README, dataset cards, and release
  notes.
- Sibling-corpus references to Hansard.

## Refresh checklist

Before a release or publication-surface change:

1. Re-run the evidence commands above.
2. Confirm no open issues or pull requests block publication.
3. Confirm `HF_REPO_ID` and `HF_HISTORICAL_REPO_ID` still differ.
4. Confirm live dataset wording still states the partial/API-discovery boundary
   unless Track 04 has authoritative full-coverage evidence.
5. Confirm historical dataset wording still states bootstrap/incomplete coverage
   unless full historical reconciliation has completed.
6. Confirm Zenodo related identifiers still point at current public surfaces.
7. Confirm OSF remains inactive or has an approved mirror policy.
8. Confirm future metadata packages, if present, are generated from current
   manifests and not hand-edited.
9. Before any GitHub repository rename, refresh
   `docs/github_repository_name_migration_assessment.md` and confirm the old
   repository URL redirects after the operation.
