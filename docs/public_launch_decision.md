# Public launch decision

Decision status: do not launch yet.

Decision date: 2026-06-07.

## Launch gate

Public launch requires every gate below to be satisfied or explicitly waived in writing.

| Gate | Current status | Evidence required |
| --- | --- | --- |
| Tracks 01-14 done or explicitly waived | Blocked | Track status review showing no unresolved blockers, or dated waiver for each blocker. See issues #10-#14. |
| Hugging Face live dataset exists | Blocked | Dataset URL, revision, manifest hash, and sample Parquet read. See issue #13. |
| Dataset scope is accurate | Blocked | Track 04 source-discovery evidence or public partial-scope wording retained everywhere. See issue #11. |
| First full or intentionally partial corpus uploaded | Blocked | Upload run URL, `manifests/latest_manifest.json`, and re-download/query proof. See issues #12 and #13. |
| GitHub scheduled sync enabled and passing | Blocked | `hf_sync.yml` run URL after first upload and scheduled-run confirmation. See issue #12. |
| Zenodo sandbox archive passed | Blocked | Sandbox draft URL, archive filename, manifest, and checksum. See issue #14. |
| Public README, dataset card, and citation files match actual coverage | Ready for current prelaunch state | README, dataset card, and citation text currently state coverage is not proven complete and avoid fixed DOI claims. Recheck after live corpus publication. |
| Monthly and annual operating checklist exists | Ready locally | `docs/maintenance_runbook.md`, `docs/reconciliation_runbook.md`, `docs/runtime_capacity_runbook.md`, and `docs/schema_governance.md`. |

## Final launch checklist

Before changing this decision to launch:

1. Confirm `conductor/tracks.md` shows Tracks 01-14 as `done` or has dated waiver notes for each blocker.
2. Record the GitHub repository URL and release/tag.
3. Record the Hugging Face dataset URL, revision, and manifest hash.
4. Run a sample Hugging Face Parquet read and save the output path or query result.
5. Confirm `hf_sync.yml` has passed after the first upload.
6. Confirm the weekly doctor workflow has passed.
7. Confirm the Zenodo sandbox archive has passed and checksums match.
8. Re-read `README.md`, `DATASET_CARD.md`, and `CITATION.cff` against the actual coverage state.
9. Keep full-coverage language out of all public pages unless Track 04 is proven.
10. Update `docs/public_launch_release_note.md` with the real URLs, dates, manifest hash, coverage count, and archive evidence.

## Evidence fields to fill at launch

```text
Launch date:
GitHub repository URL:
GitHub release or tag:
Hugging Face dataset URL:
Hugging Face revision:
Manifest hash:
Coverage statement:
Record count:
First passing scheduled sync URL:
Doctor workflow URL:
Zenodo sandbox archive URL:
Zenodo production DOI, if any:
Final reviewer:
```

## Current rationale

Launching now would overstate operational readiness. The local code and documentation are close to launch-ready, and the GitHub repository now exists at `https://github.com/edithatogo/nz-legislation-corpus-pipeline`, but the external corpus publication path is not proven: required live secrets are missing, the Hugging Face dataset has not been verified, the full corpus has not been bootstrapped, scheduled sync has not run with credentials, and Zenodo sandbox archival has not passed.

## Tracking issues

- #10 Configure required repository secrets.
- #11 Establish authoritative work-id inventory or partial-scope boundary.
- #12 Run live API smoke sync and scheduled workflow proof.
- #13 Create and verify Hugging Face dataset shell.
- #14 Prove Zenodo sandbox archive before production publication.
- #15 Make final public launch decision.
