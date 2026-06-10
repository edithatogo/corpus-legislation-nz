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
