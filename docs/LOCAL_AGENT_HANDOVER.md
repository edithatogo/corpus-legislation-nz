# Local agent handover

## Current package

Version: v0.5.0 pre-handover hardening.

This repo is ready for local-agent bootstrap once account-specific secrets and variables are available.

## Do first

1. Generate and commit a local lockfile:

   ```bash
   uv sync --extra dev --frozen
   ```

2. Run the offline smoke test:

   ```bash
   ./scripts/first_run_local.sh
   ```

3. Create the Hugging Face dataset shell:

   ```bash
   HF_TOKEN='hf_...' HF_REPO_ID='edithatogo/corpus-legislation-nz' \
     ./scripts/create_huggingface_dataset_repo.sh edithatogo/corpus-legislation-nz
   ```

4. Bootstrap the GitHub source repo:

   ```bash
   export REPO_OWNER=edithatogo
   export REPO_NAME=corpus-legislation-nz
   export REPO_VISIBILITY=public
   export HF_REPO_ID=edithatogo/corpus-legislation-nz
   export ARCHIVE_CREATORS_JSON='[{"name":"Your Name","affiliation":"Your Institution"}]'
   export NZ_LEGISLATION_API_KEY='...'
   export HF_TOKEN='...'
   export ZENODO_TOKEN='...'

   ./scripts/bootstrap_github.sh --owner "$REPO_OWNER" --repo "$REPO_NAME" --public --protect-production
   ```

## Blocking checks before first live run

- Confirm the Hugging Face repo has root-level placeholders (`parquet/`, `raw_xml/`, `manifests/`), not `data/parquet/`.
- Confirm `HF_REPO_ID` points to the dataset repo, not the GitHub source repo.
- Confirm the production Zenodo environment requires approval before publication.
- Confirm `ZENODO_DEPOSITION_ID` is blank until the first production record is published.
- Run the live sync manually with `max_works=5` before removing limits.

## Known first-run limitation

The official NZ Legislation API is search-oriented. A search-term bootstrap is not a proof of complete corpus coverage. For full coverage, prepare a seed inventory of work IDs or reconcile search discovery against an official export/source list.

## Recommended local-agent tasks

1. Run `uv sync --extra dev --frozen`, `uv run ruff check .`, `uv run pytest -q`, and `./scripts/first_run_local.sh`.
2. Create the Hugging Face dataset shell and verify root layout.
3. Create the GitHub repo and configure secrets/variables.
4. Manually run `Hugging Face live sync` with `max_works=5`.
5. Inspect Hugging Face files and manifests.
6. Expand source discovery using seed work IDs or staged search reconciliation.
7. Run a Zenodo sandbox archive workflow with `publish=false`.
8. Only after review, configure production Zenodo publication approval.
