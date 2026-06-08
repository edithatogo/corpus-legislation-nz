# Local agent handoff

## Objective

Finish bootstrapping the NZ legislation corpus pipeline with minimum long-term maintenance burden.

## Immediate P0 tasks before creating the GitHub repo

1. Run `scripts/pre_handoff_check.sh` from the repository root.
2. Confirm `uv.lock` is committed and CI install steps avoid optional heavyweight extras unless the workflow exercises them.
3. Confirm the Hugging Face repository layout is root-based:
   - `parquet/`
   - `raw_xml/`
   - `manifests/`
   - `_state/`
4. Do not commit `data/`, `dist/`, `.venv/`, `.hf_cache/`, `__pycache__/`, or `*.pyc`.

## P1 tasks after creating the GitHub and Hugging Face repositories

1. Create a fine-grained Hugging Face token scoped only to the target dataset repo.
2. Create separate Zenodo sandbox and production tokens when possible; store them as environment secrets.
3. Configure `zenodo-production` with a required reviewer and prevent self-review if available.
4. Run fixture smoke test locally:

   ```bash
   ARCHIVE_CREATORS_JSON='[{"name":"Test Maintainer"}]' NZLC_OUTPUT_DIR=data uv run nzlc smoke-fixture --output-dir data
   NZLC_OUTPUT_DIR=data uv run nzlc validate
   NZLC_OUTPUT_DIR=data uv run nzlc manifest
   NZLC_OUTPUT_DIR=data uv run nzlc coverage-report
   ```

5. Run GitHub Actions manual Hugging Face sync with `max_works=5` before enabling full daily schedule.
   - For the first run, also set `NZLC_MIN_SECONDS_BETWEEN_REQUESTS=1.0` or use the workflow input override.
6. Inspect the Hugging Face dataset viewer and sample Parquet reads.
7. Run the Zenodo workflow against sandbox only; verify archive, manifest, and checksum files.

## P1 source-discovery contract

The current API client is intentionally conservative because the NZ Legislation API is search-oriented. The local agent must not treat a few broad search terms as proof of complete corpus coverage.

Acceptance criteria:

- A deterministic `seeds/work_ids.txt` is created or a documented discovery method proves coverage.
- Coverage report includes counts by legislation type, status, year, missing text, missing XML URL, and ephemeral identifiers.
- Ephemeral IDs containing `~` are counted and surfaced in the report.
- First production full sync is performed in staged batches to respect rate limits.
- First manual bootstrap sync uses `seeds/work_ids.txt`, `max_works=5`, and a higher request spacing override.

## P2 improvements

- Extend mocked HTTP tests for any remaining API edge cases, including format-link parsing if needed.
- Add archive provenance/attestation once the production publication path is stable.
- Add a manual runbook for generating a Hugging Face DOI after the live repository is stable, while keeping Zenodo as the annual immutable archive.
- Pin GitHub Actions to full commit SHAs if the maintainer prefers stronger supply-chain security over easier Dependabot maintenance.

## Definition of done for handover

- GitHub repo created from a clean working tree.
- Hugging Face dataset repo initialized.
- `uv.lock` committed.
- CI tests pass.
- Manual smoke sync with `max_works=5` passes.
- Zenodo sandbox draft upload passes.
- `README.md`, `DATASET_CARD.md`, `docs/source_discovery_strategy.md`, and this handoff file are reviewed.
