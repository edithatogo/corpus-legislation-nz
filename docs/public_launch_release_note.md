# Draft public launch release note

Status: draft only. Do not publish until `docs/public_launch_decision.md` is changed to a launch decision with live evidence.

## New Zealand Legislation Corpus

The New Zealand Legislation Corpus is an API-first pipeline and dataset for machine-readable New Zealand legislation records. It publishes normalized records, source provenance, optimized Parquet files, validation reports, coverage metrics, and manifest hashes for reproducible research use.

## Coverage

Coverage status at launch: intentionally partial/API-discovery based unless Track 04 later proves a complete authoritative inventory.

Do not claim full New Zealand legislation coverage unless Track 04 has proven the discovery method against an authoritative inventory. If Track 04 is not proven, state the dataset is partial or API-discovery based and include the configured discovery boundary.

Fields to fill:

```text
Record count: 6
Legislation types included: act
Statuses included: in_force, not_in_force
Discovery method: API-first search/discovery workflow; no authoritative seed inventory yet
Known gaps: full New Zealand legislation coverage is not proven; no authoritative seeds/work_ids.txt exists
Manifest hash: 134b6cbca7a6703a512f914288fbdad2d6638e2f9048bef24c45371af0b647a2
Hugging Face revision: 8d48d807c5c8da73f8ad164734245d9ea73046f3
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

For fixed-version academic citation, cite the annual Zenodo DOI snapshot once available.

## Archive plan

The live dataset is maintained on Hugging Face. Annual immutable snapshots are intended for Zenodo DOI-backed archival release after production-draft verification and production approval.
