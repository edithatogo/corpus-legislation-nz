# Zenodo Rights Metadata And Zenodraft Workflow

Date: 2026-06-10.

This document records the Track 27 decision for Zenodo rights metadata and
future `zenodraft` adoption. It preserves the current published DOI while
making the next annual snapshot workflow more explicit about source-content
rights, draft-first operation, and protected publication.

## Current Zenodo Record

Current published record:

- Record: `https://zenodo.org/records/20592540`.
- DOI: `10.5281/zenodo.20592540`.
- Concept DOI: `10.5281/zenodo.20592539`.
- Title: `New Zealand Legislation Corpus: 2026 annual snapshot`.
- Publication date: `2026-06-08`.
- Resource type: dataset.
- Access: open.
- Published Zenodo API license metadata: `cc-by-4.0`.
- Zenodraft/Zenodo metadata-schema license identifier: `CC-BY-4.0`.
- Related identifier:
  `https://huggingface.co/datasets/edithatogo/corpus-legislation-nz`.
- Published archive filenames still use the earlier
  `nz-legislation-corpus-2026` prefix and must remain immutable.

The current DOI and files must not be renamed, replaced, or unpublished. Future
metadata correction should use a new Zenodo version or metadata update only
where Zenodo permits it and the public evidence ledger is updated.

## Rights Scope

The project separates rights by artifact class:

| Artifact class | Rights position |
| --- | --- |
| Repository code | MIT, as stated in `pyproject.toml` and repository license metadata. |
| Documentation and schemas | Repository documentation, unless a file states otherwise; do not use this to relicense source legislation text. |
| Pipeline manifests and checksums | Generated project metadata; may be shared with the archive under the Zenodo record's metadata license statement. |
| Normalized Parquet and JSONL records | Derived from official source material; dataset publication does not relicense source legislation text or third-party material. |
| Raw XML/HTML source snapshots | Source-derived material; retain source URL/provenance and official NZ Legislation rights caveats. |
| Incorporated-by-reference or linked third-party material | Not covered by the project license; may be excluded or subject to separate rights. |
| Archive bundle | Packaging of the above; Zenodo `cc-by-4.0` metadata should be read as applying to project-created metadata, packaging, manifests, and permitted source material, not as a blanket relicense of all upstream content. |

Decision: keep `ARCHIVE_LICENSE=cc-by-4.0` for the current publication line and
use `CC-BY-4.0` in zenodraft-validated metadata JSON, but every public surface
must carry the scope note above. If a future reviewer decides that Zenodo's
license field overstates the upstream text rights, use a new protected-track
decision to switch future records to a different Zenodo rights statement. Do not
change the current DOI record casually.

## Zenodraft Evaluation

`zenodraft` was evaluated from `https://github.com/zenodraft/zenodraft` on
2026-06-10.

Observed local toolchain:

- Node: `v24.15.0`.
- npm: `11.12.1`.
- `npx --yes zenodraft --help` works.
- `npx --yes zenodraft metadata validate --help` confirms local metadata
  validation.
- `npx --yes zenodraft deposition create --help` confirms concept and version
  draft creation commands.
- `npx --yes zenodraft deposition show --help` confirms draft, files,
  prereserved DOI, and details readback commands.

Adoption decision:

- Do not add `zenodraft` to Python dependencies.
- Use a Node-only CI step when the annual Zenodo workflow is migrated.
- Prefer `npx --yes zenodraft@latest` only for manual evaluation and
  time-bounded experiments.
- For production CI, pin a known working npm package version or commit in the
  future migration PR before replacing the Python uploader.
- Keep the existing Python uploader until a sandbox `zenodraft` draft/version
  proof has passed.

## Token Mapping

`zenodraft` expects platform-specific access-token environment variables. The
existing repository secrets should be mapped only inside the relevant workflow
step:

```bash
if [ "$ZENODO_ENV" = "sandbox" ]; then
  export ZENODO_SANDBOX_ACCESS_TOKEN="$ZENODO_SANDBOX_TOKEN"
  unset ZENODO_TOKEN
else
  export ZENODO_ACCESS_TOKEN="$ZENODO_TOKEN"
  unset ZENODO_SANDBOX_TOKEN
fi
```

Do not expose both production and sandbox tokens to a step that only needs one.
Do not echo token values.

## Draft Workflow Target

Future `zenodraft` migration should use this sequence:

1. Build archive files with `uv run nzlc archive`.
2. Generate or update a local Zenodo metadata JSON file.
3. Validate metadata:
   `npx --yes zenodraft metadata validate docs/zenodo/zenodo-2026-metadata.example.json`.
4. For a new concept in sandbox:
   `npx --yes zenodraft deposition create concept --sandbox`.
5. For a new version in sandbox:
   `npx --yes zenodraft deposition create version --sandbox <concept_id>`.
6. Upload files:
   `npx --yes zenodraft file add --sandbox <version_id> <file>`.
7. Update metadata:
   `npx --yes zenodraft metadata update --sandbox <version_id> <metadata.json>`.
8. Capture evidence:
   `npx --yes zenodraft deposition show prereserved --sandbox <version_id>`.
9. Capture details:
   `npx --yes zenodraft deposition show details --sandbox <version_id>`.

The sandbox proof must record the draft/version ID, prereserved DOI, file list,
metadata validation result, and whether the archive file checksums match the
generated checksum file.

## Protected Publication Gate

Publication must remain a separate action:

- Ordinary scheduled and manual archive runs create or update a draft only.
- Production publish requires `publish=true`.
- Production publish must run through the `zenodo-production` GitHub
  environment.
- The `zenodo-production` environment must require reviewer approval.
- `zenodraft deposition publish` must not appear in ordinary upload/update
  steps.

The current `.github/workflows/annual_zenodo_archive.yml` remains draft-first by
default. It may continue using the Python uploader until the sandbox
`zenodraft` proof is complete.

## Publication Surface Alignment

- GitHub remains the workflow and evidence controller.
- Hugging Face remains the live operational dataset.
- Zenodo remains the fixed annual DOI snapshot surface.
- OSF remains inactive unless a future mirror/review policy is approved.
- Future Croissant, RO-Crate, Frictionless, DCAT, and PROV-O metadata packages
  must carry the same rights-scope caveat and cite the source manifest hash.

Preferred corpus-family labels remain `corpus-nz-legislation` and
`corpus-nz-hansard`. Current public legislation surfaces remain
`corpus-legislation-nz` until a separate migration plan protects citations and
redirects.
