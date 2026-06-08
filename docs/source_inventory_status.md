# Source inventory status

Checked: 2026-06-08

## Current source

The official New Zealand Legislation API is the current source-of-truth intake path for this pipeline.

Public documentation checked on 2026-06-08 describes the API as equivalent to the website search function and lists these endpoints:

- `/v0/works`: search for works.
- `/v0/works/{work_id}/versions`: get all versions of a work.
- `/v0/versions/{version_id}`: get one version.

The public documentation did not identify a complete work-ID export, full bulk inventory endpoint, or modified-since enumeration endpoint.

## Current inventory status

No authoritative `seeds/work_ids.txt` is currently present in this repository.

The examples under `seeds/` are format examples only. They are not a complete inventory and must not be used as proof of coverage.

## Coverage implication

Until an official export, authoritative inventory, or fully reconciled seed list exists, the project must describe itself as an automated API-first corpus pipeline, not a proven complete New Zealand legislation corpus.

For the current launch gate, the intended public boundary is therefore an intentionally partial/API-discovery dataset. The Hugging Face corpus can be used as live operational evidence, but it is not evidence of full New Zealand legislation coverage.

## Required next step

Obtain one of the following before closing Track 04:

- an official work-ID export from the NZ Legislation or Parliamentary Counsel Office team;
- a complete authoritative inventory that can be transformed into `seeds/work_ids.txt` with provenance; or
- a documented reconciliation proving that API search discovery covers the intended corpus boundaries.
