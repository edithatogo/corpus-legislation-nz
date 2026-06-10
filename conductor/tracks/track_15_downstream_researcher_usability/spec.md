# Spec - Downstream Researcher Usability

## Status
blocked

## Goal
make the published corpus easy to inspect and query after the live hub is stable.

## Acceptance Criteria
- A new user can query the Parquet dataset without downloading the full raw corpus.
- Examples are tested or manually verified.
- Optional browser UI is clearly secondary to the dataset pipeline.

## Evidence to Record
- Example command output.
- Sample dataset path or revision.
- Documentation links.

## Evidence Recorded

- Documentation added on 2026-06-07:
  - `docs/researcher_quickstart.md`
  - `docs/data_dictionary.md`
- Documentation links added:
  - `README.md` links to researcher quickstart and data dictionary.
  - `DATASET_CARD.md` points core field definitions to the data dictionary.
- Researcher examples:
  - DuckDB examples show `hf://datasets/REPLACE-ME/corpus-legislation-nz/parquet/**/*.parquet` queries.
  - PyArrow example shows local `data/parquet` reads with Hive partitioning.
  - Local smoke fixture commands show how to generate a tiny non-network Parquet corpus for tooling checks.
- Sample split decision:
  - Do not add a public sample split yet. A sample should be published only after the live Hugging Face dataset exists, so it is not mistaken for coverage evidence.
- Optional browser UI decision:
  - Do not add a Hugging Face Space yet. Browser/search UI remains secondary until the dataset pipeline and live hub are stable.

## Blocked Items

- Cannot verify Hugging Face DuckDB query output until the dataset repository and full upload exist.
- Cannot record sample dataset path or revision until the Hugging Face dataset is published.
- Cannot publish or validate a public sample split until Track 08 creates the live dataset state.
- Cannot build a meaningful browser UI until the corpus is published and stable enough to browse.
