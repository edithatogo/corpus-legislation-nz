# OSF Optional Mirror Policy

## Status

**Inactive** — OSF is an optional convenience mirror. This document defines the convenience mirror policy for the
Open Science Framework (OSF). No OSF project has been created yet. All
references to OSF as a publication surface remain optional and pending a
future implementation track.

OSF is inactive by default and must not become a second source of truth
for the corpus.

## Purpose

OSF provides a supplementary mirror for the code repository and the
published corpus dataset. It is not a canonical publication surface;
GitHub remains the source of truth for code, workflows, issues, release
evidence, and maintainer-facing documentation. Hugging Face is the live
operational dataset and Zenodo is the immutable
DOI snapshot archive.

## When to use OSF

1. **Code mirror**: Push a read-only copy of the GitHub repository to OSF
   as an additional access point for researchers who prefer OSF's
   discovery and review workflows.
2. **Dataset mirror**: Upload a copy of the latest validated corpus
   snapshot to OSF as a convenience download surface, provided the
   single-file size limit is respected (see below).

## File size constraint

OSF has a per-file upload limit of **5 GB**. The `osf_optional.py` module
in `src/nz_legislation_corpus/` provides an `assert_osf_file_sizes()`
check that refuses mirror uploads when any file exceeds this limit.

If a corpus archive or metadata package exceeds 5 GB, it must be split
into multiple files before mirroring to OSF.

## What not to mirror to OSF

- Raw XML/HTML source files larger than 5 GB (these should remain on
Hugging Face Xet-backed storage).
- Partial or unreviewed batch outputs — only validated, full-corpus
  snapshots should be mirrored.
- Secrets, credentials, or private workflow state.

## Relation to other publication surfaces

| Surface | Role | OSF relation |
|---------|------|-------------|
| GitHub | Source code, CI/CD, schemas, tests, docs | OSF code mirror sourced from GitHub |
| Hugging Face | Live operational dataset (Parquet, XML, manifests) | OSF dataset mirror sourced from validated Hugging Face snapshot |
| Zenodo | Immutable annual DOI archive | Independent; OSF not a replacement |
| OSF | Optional convenience mirror | This document |

Hugging Face remains the canonical live dataset surface. Zenodo remains
the immutable citation surface.

## OSF project structure (proposed)

If implemented, the OSF project should use a flat layout:

```
osf-project/
  README.md                          # Links to canonical GitHub + Hugging Face
  corpus-legislation-nz-YYYY.tar.gz  # Annual validated archive snapshot
  corpus-legislation-nz-YYYY.SHA256SUMS
  corpus-legislation-nz-YYYY.release-evidence.json
```

No component directory is required inside OSF; the project is a
convenience pointer with optional archive snapshots.

## Activation criteria

OSF mirroring should be activated only when:

1. The full corpus bootstrap (Track 07) is complete and validated.
2. The full Hugging Face corpus upload (Track 08) is published.
3. A maintainer has created an OSF project and generated an access token.
4. A tracked OSF implementation issue or track exists in Conductor.

Until all four criteria are met, OSF remains an optional policy document
only.

## Validation and gates

The local file-size guard is implemented in
`src/nz_legislation_corpus/osf_optional.py`, with a default 5 GB per-file
limit. OSF mirror bundles should include SHA-256 checksums for every archive
part.

Live OSF setup, uploads, account linking, browser-profile work, and token
configuration are gated external-account operations. They require explicit
user approval for the specific action.

Run the local policy validator with:

```powershell
python scripts/check_osf_optional_policy.py
```
