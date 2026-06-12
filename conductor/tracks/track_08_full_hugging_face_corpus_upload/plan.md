# Plan - Full Hugging Face Corpus Upload

## Tasks
- [x] Confirm upload helper defaults `HF_XET_HIGH_PERFORMANCE=1`.
- [ ] Run `uv run nzlc hf-upload` for the full validated corpus.
- [ ] Use resumable upload behavior if the upload is interrupted.
- [ ] Verify Hugging Face contains `parquet/`, `raw_xml`, `records.jsonl`,
  `manifests/`, and `_state/` as expected for the full corpus.
- [ ] Re-download the dataset into a clean location and compare manifest hashes.
- [ ] Confirm the dataset card states the discovery and coverage status
  accurately.

## Current blocker

- A live partial/API-discovery Hugging Face dataset exists, but no full
  validated corpus has been produced.
- Track 07 must complete first to produce the full local corpus and manifest.
- Full publication must not overwrite the partial/live scope with an
  unreviewed or unreconciled search-derived corpus.


## Implementation automation added 2026-06-12

- Added `.github/workflows/full_corpus_hf_upload.yml` as the full live upload workflow.
- The workflow defaults to `upload_confirmed=false` review mode and only calls `uv run nzlc hf-upload` when explicitly confirmed.
- The post-upload verification step downloads the remote manifest and compares it with the local manifest.
- See `docs/full_corpus_operations.md` for the operator inputs and review
  sequence for this workflow.
- Track is `ready` but still requires a real full-corpus artifact from Track 07 before confirmed publication.
