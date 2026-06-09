# Public launch decision

Decision status: launch approved for the intentional partial/API-discovery
dataset.

Decision date: 2026-06-09.

## Launch gate

Public launch requires every gate below to be satisfied or explicitly waived in writing.

| Gate | Current status | Evidence required |
| --- | --- | --- |
| Tracks 01-14 done or explicitly waived | Ready for intentional partial/API-discovery launch | Track blockers that would overstate full coverage remain out of public wording. The scheduled-run gate in issue #12 was explicitly waived by the repository owner on 2026-06-09. See issues #10-#14. |
| Hugging Face live dataset exists | Ready | Dataset URL: `https://huggingface.co/datasets/edithatogo/nz-legislation-corpus`; revision: `8d48d807c5c8da73f8ad164734245d9ea73046f3`; manifest hash: `134b6cbca7a6703a512f914288fbdad2d6638e2f9048bef24c45371af0b647a2`; sample Parquet read passed. See issue #13. |
| Dataset scope is accurate | Ready for intentional partial/API-discovery launch | No authoritative `seeds/work_ids.txt` exists and current public wording retains the partial/API-discovery boundary. See issue #11 and `docs/source_inventory_status.md`. |
| First full or intentionally partial corpus uploaded | Ready for intentional partial/API-discovery launch | `hf_sync.yml` uploaded a six-record validated corpus. Current content hash: `da764d2dc63a86b6da00d573843abe33e27d73bc80254bef65ca837316a83ebc`; current record count: 6. See issues #12 and #13. |
| GitHub scheduled sync enabled and passing | Waived on 2026-06-09 | Manual live sync, restore/no-change, manifest, coverage, and upload proof passed. The first post-fix scheduled event did not dispatch after the temporary accelerated cron and stale-run cancellation, so the repository owner explicitly waived this launch gate on 2026-06-09. See issue #12. |
| Zenodo production archive published | Ready | Published record: `https://zenodo.org/records/20592540`; DOI: `10.5281/zenodo.20592540`; concept DOI: `10.5281/zenodo.20592539`; run: `https://github.com/edithatogo/nz-legislation-corpus-pipeline/actions/runs/27132519663`; archive, manifest, and checksum files are present. See issue #14. |
| Public README, dataset card, and citation files match actual coverage | Ready for intentional partial/API-discovery launch | README, dataset card, and citation text state coverage is not proven complete and cite the Zenodo DOI only as the fixed-version snapshot. |
| Monthly and annual operating checklist exists | Ready locally | `docs/maintenance_runbook.md`, `docs/reconciliation_runbook.md`, `docs/runtime_capacity_runbook.md`, and `docs/schema_governance.md`. |

## Final launch checklist

Completed launch evidence:

1. Confirm `conductor/tracks.md` shows Tracks 01-14 as `done` or has dated waiver notes for each blocker.
2. Record the GitHub repository URL and release/tag.
3. Record the Hugging Face dataset URL, revision, and manifest hash.
4. Run a sample Hugging Face Parquet read and save the output path or query result.
5. Confirm `hf_sync.yml` has passed after the first upload, or record an explicit waiver.
6. Confirm the weekly doctor workflow has passed.
7. Confirm the Zenodo production archive has passed and checksums match.
8. Re-read `README.md`, `DATASET_CARD.md`, and `CITATION.cff` against the actual coverage state.
9. Keep full-coverage language out of all public pages unless Track 04 is proven.
10. Update `docs/public_launch_release_note.md` with the real URLs, dates, manifest hash, coverage count, and archive evidence.

## Evidence fields to fill at launch

```text
Launch date: 2026-06-09
GitHub repository URL: https://github.com/edithatogo/nz-legislation-corpus-pipeline
GitHub release or tag: v0.1.0-partial.20260609; https://github.com/edithatogo/nz-legislation-corpus-pipeline/releases/tag/v0.1.0-partial.20260609
Hugging Face dataset URL: https://huggingface.co/datasets/edithatogo/nz-legislation-corpus
Hugging Face revision: 8d48d807c5c8da73f8ad164734245d9ea73046f3
Manifest hash: 134b6cbca7a6703a512f914288fbdad2d6638e2f9048bef24c45371af0b647a2
Coverage statement: intentional partial/API-discovery corpus; full New Zealand legislation coverage is not proven
Record count: 6
First passing scheduled sync URL: waived by repository owner on 2026-06-09
Doctor workflow URL: https://github.com/edithatogo/nz-legislation-corpus-pipeline/actions/runs/27116561990
Zenodo production archive URL: https://zenodo.org/records/20592540
Zenodo production DOI: 10.5281/zenodo.20592540
Final reviewer: repository owner waiver plus maintainer review
```

## Current rationale

Launch is approved for the intentional partial/API-discovery dataset. The GitHub
repository exists at `https://github.com/edithatogo/nz-legislation-corpus-pipeline`,
the Hugging Face dataset exists with a verified six-record corpus, and the
Zenodo production archive has been published. Full New Zealand legislation
coverage is not claimed. The first scheduled sync proof did not complete and was
explicitly waived by the repository owner on 2026-06-09.

## Tracking issues

- #10 Configure required repository secrets.
- #11 Establish authoritative work-id inventory or partial-scope boundary.
- #12 Run live API smoke sync and scheduled workflow proof.
- #13 Create and verify Hugging Face dataset shell.
- #14 Prove Zenodo production draft archive before publication.
- #15 Make final public launch decision.
