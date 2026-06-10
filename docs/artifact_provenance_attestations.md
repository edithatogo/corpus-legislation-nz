# Artifact provenance and attestations

Track 33 defines the release evidence and attestation policy for
`corpus-nz-legislation`, aligned with the sibling `corpus-nz-hansard` corpus
family. The policy records enough evidence for users to connect a public
artifact back to a repository commit, workflow run, manifest hash, coverage
statement, and publication surface.

Publication remains behind validation gates. This track does not weaken the
manual Hugging Face upload rules, the historical upload guardrails, or the
protected Zenodo production environment.

## Release evidence ledger

Every annual archive build writes:

- `corpus-legislation-nz-YYYY.tar.zst` or `.tar.gz`;
- `corpus-legislation-nz-YYYY.manifest.json`;
- `corpus-legislation-nz-YYYY.release-evidence.json`;
- `corpus-legislation-nz-YYYY.SHA256SUMS.txt`.

The release evidence file follows
`schemas/release_evidence.schema.json` and records:

- source repository, commit SHA, workflow name, workflow run ID, run attempt,
  ref, and triggering event;
- Hugging Face repository and revision where known;
- Zenodo DOI and concept DOI where known;
- manifest hash, content hash, schema version, record schema version, record
  count, and coverage statement;
- SHA-256 and size for archive subjects;
- the attestation strategy for the artifact class.

`SHA256SUMS` remains the portable checksum ledger. It covers the archive,
manifest, and release evidence file.

## Artifact-class policy

| Artifact class | Examples | Provenance strategy | Status |
| --- | --- | --- | --- |
| Annual Zenodo archive | `.tar.zst` or `.tar.gz`, manifest, release evidence, `SHA256SUMS` | GitHub artifact attestation plus release evidence JSON plus SHA-256 checksums | Adopted for GitHub Actions archive builds. |
| Hugging Face live dataset | Parquet, raw XML/HTML, `records.jsonl`, manifests | Manifest hash, HF revision, workflow/run evidence, dataset card; GitHub artifact attestation is not directly applicable to remote HF objects | Deferred until HF publication workflow emits a release evidence file after upload. |
| Historical Hugging Face dataset | Historical Parquet/raw records and manifests | Dry-run artifact review, manifest hash, HF revision after upload; GitHub artifact attestation is not directly applicable to remote HF objects | Deferred until historical upload policy is mature. |
| Metadata packages | Croissant, RO-Crate, Frictionless, DCAT, PROV-O, `SHA256SUMS` | SHA-256 checksums and metadata-package manifest now; GitHub artifact attestation when attached to a release/archive workflow | Ready for future release workflow. |
| Source code/package | GitHub repository, Python package if published later | Git tag/release, package version, CodeQL/Scorecard/quality checks; artifact attestation if wheel/sdist publication is added | Deferred because the project currently publishes datasets, not Python packages. |

GitHub artifact attestation is implemented in
`.github/workflows/annual_zenodo_archive.yml` using the official GitHub
attestation action after the archive is built and before the Zenodo draft upload
step. The workflow has `contents: read`, `attestations: write`, and
`id-token: write`; it does not grant general write access.

SLSA-style provenance is represented by the release evidence JSON plus GitHub's
OIDC-backed artifact attestation. Full SLSA release certification is not claimed.

Cryptographic signing beyond GitHub artifact attestations is deferred. The
portable baseline is SHA-256 checksums in `SHA256SUMS`; detached GPG or Sigstore
signatures can be added later if the project adopts a key-management policy.

## Validation

Local policy and schema checks:

```powershell
uv run python scripts\check_artifact_provenance.py
```

Archive generation check:

```powershell
uv run nzlc archive --year 2026 --output-dir dist/archive
```

The checker validates the release evidence JSON Schema, confirms this policy
names the required public-surface evidence fields, checks that the annual Zenodo
workflow has artifact-attestation permissions and steps, and validates any local
`dist/archive/*.release-evidence.json` files that exist.

## Zenodo and zenodraft boundary

Zenodo publication remains draft-first. Production publication still requires
the protected `zenodo-production` environment and explicit `publish=true`.

Track 27 formally evaluated `zenodraft`; this provenance policy keeps that
decision in scope by requiring Zenodo archive evidence to include the manifest,
checksums, release evidence file, DOI/concept DOI where known, and validation
gate status.
