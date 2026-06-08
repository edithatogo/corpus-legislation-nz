# Hugging Face setup

This project uses Hugging Face Datasets as the live operational data hub. GitHub stores code and workflows; Hugging Face stores the evolving corpus.

## Target dataset repository

Recommended default:

```text
edithatogo/nz-legislation-corpus
```

This target is for the live partial/API-discovery corpus line. Historical corpus
pilots must not upload over it; see `docs/historical_publication_policy.md`.

## What can be automated

The repository can be created and initialised through the Hugging Face API or CLI once `HF_TOKEN` is available. The included script creates the dataset repository, uploads a dataset card, sets `.gitattributes`, creates lightweight placeholder directories at repository root, and removes any older `data/...` bootstrap placeholders.

```bash
export HF_TOKEN="hf_..."
export HF_REPO_ID="edithatogo/nz-legislation-corpus"
export HF_PRIVATE="false"
./scripts/create_huggingface_dataset_repo.sh "$HF_REPO_ID"
```

The script is idempotent: rerunning it updates the metadata shell but does not upload corpus data.

## Remote repository layout

The Hugging Face repository is stored at repository root, not under an extra `data/` prefix:

```text
records.jsonl
parquet/
raw_xml/
manifests/
_state/
```

The GitHub workflow downloads that repository into a local `data/` working directory, so remote `manifests/latest_manifest.json` becomes local `data/manifests/latest_manifest.json`.

## What the GitHub workflow will do

The `hf_sync.yml` workflow will:

1. run the NZ Legislation API sync;
2. validate records;
3. write stable partitioned Parquet;
4. generate manifests and coverage reports;
5. upload the corpus folder to Hugging Face with `hf upload-large-folder`.

## Why Xet matters

Hugging Face Hub uses Xet-backed storage for large files. Xet deduplicates content at the chunk level, so stable Parquet files with stable ordering reduce repeat upload cost. This is why the pipeline avoids daily monolithic archives and instead writes stable partitions.

## Required GitHub secret

```text
HF_TOKEN
```

The token needs write access to the dataset repo.

## Required GitHub variable

```text
HF_REPO_ID=edithatogo/nz-legislation-corpus
```

## Recommended first checks

After creating the dataset repo:

```bash
uv run nzlc doctor --network
./scripts/first_run_local.sh
```

Then trigger the GitHub workflow manually once the GitHub repository exists and the NZ Legislation API key is configured.

## Manual fallback upload

```bash
export HF_TOKEN="hf_..."
export HF_REPO_ID="edithatogo/nz-legislation-corpus"
export HF_XET_HIGH_PERFORMANCE=1
uv run nzlc hf-upload
```

## Do not manually edit data files

Manual edits in the Hugging Face dataset can be overwritten by the next successful pipeline run. Treat the GitHub pipeline as the source of truth for publication logic.
