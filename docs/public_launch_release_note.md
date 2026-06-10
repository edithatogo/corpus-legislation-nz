# Public launch release note

Status: launch approved on 2026-06-09 for the intentional partial/API-discovery
dataset. The scheduled-sync launch gate was explicitly waived by the repository
owner on 2026-06-09.

## New Zealand Legislation Corpus

The New Zealand Legislation Corpus is an API-first pipeline and dataset for machine-readable New Zealand legislation records. It publishes normalized records, source provenance, optimized Parquet files, validation reports, coverage metrics, and manifest hashes for reproducible research use.

## Coverage

Coverage status at launch: intentionally partial/API-discovery based unless Track 04 later proves a complete authoritative inventory.

Do not claim full New Zealand legislation coverage unless Track 04 has proven the discovery method against an authoritative inventory. If Track 04 is not proven, state the dataset is partial or API-discovery based and include the configured discovery boundary.

Fields to fill:

```text
GitHub release tag: v0.1.0-partial.20260609
Record count: 6
Legislation types included: act
Statuses included: in_force, not_in_force
Discovery method: API-first search/discovery workflow; no authoritative seed inventory yet
Known gaps: full New Zealand legislation coverage is not proven; no authoritative seeds/work_ids.txt exists
Manifest hash: 134b6cbca7a6703a512f914288fbdad2d6638e2f9048bef24c45371af0b647a2
Hugging Face revision: 6b082e2f85802cb374898d689d264017a047799b
Zenodo DOI: 10.5281/zenodo.20592540
Zenodo record: https://zenodo.org/records/20592540
Scheduled sync gate: waived by repository owner on 2026-06-09
```

## Caveats

- This dataset is not legal advice.
- Text extraction is conservative and may not preserve every legal structure.
- Coverage is limited to the verified discovery scope.
- Incorporated-by-reference material, third-party material, agency website text, logos, emblems, and non-legislative linked content may have separate rights or restrictions.
- Users should cite the manifest hash for live/current use.

## Update cadence

The intended operating model is:

- daily or regular Hugging Face sync after the first verified upload;
- weekly non-destructive service doctor checks;
- monthly coverage/reconciliation review;
- annual Zenodo archive workflow, production draft first and publication only after approval.

## Citation

For live/current use, cite:

```text
New Zealand Legislation Corpus, Hugging Face dataset URL, access date, and manifest hash.
```

For fixed-version academic citation, cite the Zenodo snapshot DOI: `10.5281/zenodo.20592540`.

## Archive plan

The live dataset is maintained on Hugging Face. Annual immutable snapshots are published to Zenodo for DOI-backed archival release. The 2026 snapshot is published at `https://zenodo.org/records/20592540`.
