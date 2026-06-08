# Public launch decision

Decision status: do not launch yet.

Decision date: 2026-06-08.

## Launch gate

Public launch requires every gate below to be satisfied or explicitly waived in writing.

| Gate | Current status | Evidence required |
| --- | --- | --- |
| Tracks 01-14 done or explicitly waived | Blocked | Track status review showing no unresolved blockers, or dated waiver for each blocker. See issues #10-#14. |
| Hugging Face live dataset exists | Ready | Dataset URL: `https://huggingface.co/datasets/edithatogo/nz-legislation-corpus`; revision: `8d48d807c5c8da73f8ad164734245d9ea73046f3`; manifest hash: `134b6cbca7a6703a512f914288fbdad2d6638e2f9048bef24c45371af0b647a2`; sample Parquet read passed. See issue #13. |
| Dataset scope is accurate | Ready for intentional partial/API-discovery launch | No authoritative `seeds/work_ids.txt` exists and current public wording retains the partial/API-discovery boundary. See issue #11 and `docs/source_inventory_status.md`. |
| First full or intentionally partial corpus uploaded | Ready for intentional partial/API-discovery launch | `hf_sync.yml` uploaded a six-record validated corpus. Current content hash: `da764d2dc63a86b6da00d573843abe33e27d73bc80254bef65ca837316a83ebc`; current record count: 6. See issues #12 and #13. |
| GitHub scheduled sync enabled and passing | Blocked | `hf_sync.yml` run URL after first upload and scheduled-run confirmation. See issue #12. |
| Zenodo production draft archive passed | Ready | Production draft URL: `https://zenodo.org/deposit/20592540`; run: `https://github.com/edithatogo/nz-legislation-corpus-pipeline/actions/runs/27132519663`; publish requested: false; uploaded archive, manifest, and checksum files. See issue #14. |
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
7. Confirm the Zenodo production draft archive has passed and checksums match.
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
Zenodo production draft archive URL: https://zenodo.org/deposit/20592540
Zenodo production DOI, if any:
Final reviewer:
```

## Current rationale

Launching now would still overstate operational readiness. The GitHub repository exists at `https://github.com/edithatogo/nz-legislation-corpus-pipeline`, the Hugging Face dataset now exists with a verified intentionally partial/API-discovery corpus, and the Zenodo production draft archive has passed with `publish=false`. Full coverage is not claimed. Launch remains blocked because the first scheduled sync proof has not completed.

## Tracking issues

- #10 Configure required repository secrets.
- #11 Establish authoritative work-id inventory or partial-scope boundary.
- #12 Run live API smoke sync and scheduled workflow proof.
- #13 Create and verify Hugging Face dataset shell.
- #14 Prove Zenodo production draft archive before publication.
- #15 Make final public launch decision.
