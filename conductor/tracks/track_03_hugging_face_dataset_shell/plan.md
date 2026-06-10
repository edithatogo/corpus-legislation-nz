# Plan - Hugging Face Dataset Shell

## Tasks
- [ ] Create or confirm the Hugging Face dataset repository named by `HF_REPO_ID`.
- [ ] Run `scripts/create_huggingface_dataset_repo.sh "$HF_REPO_ID"` or equivalent API setup.
- [ ] Confirm the remote layout is root-based, not nested under `data/`.
- [ ] Confirm `.gitattributes`, dataset card metadata, and lightweight root placeholders are correct.
- [ ] Remove any legacy `data/...` placeholders if present.

## Current blocker

- `HF_REPO_ID` is not configured in the local environment.
- `HF_TOKEN` is not configured in the local environment.
- The existing setup script is ready and idempotent, but it cannot run to completion without the final dataset ID and a write-capable Hugging Face token.
- Public search/open checks on 2026-06-07 did not confirm an existing public `edithatogo/corpus-legislation-nz` dataset shell.
