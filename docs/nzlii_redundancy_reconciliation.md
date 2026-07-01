# NZLII Redundancy Reconciliation

Track 39 treats NZLII as a secondary, corroborating source for coverage
comparison and manual triage. It does not replace official NZ Legislation
records.

## Candidate Record Shape

NZLII candidate match records carry:

- `url`
- `title`
- `date`
- `retrieved_at`
- `content_hash`
- `confidence`
- `classification`

## Matching Rules

The reconciliation helpers in `src/nz_legislation_corpus/nzlii_reconcile.py`
classify each official record against the NZLII candidate set as one of:

- `exact`
- `probable`
- `ambiguous`
- `missing`
- `out_of_scope`

The helpers are deterministic and operate only on supplied metadata. Tests do
not scrape NZLII or require live network access.

## Report Output

The generated reconciliation report keeps NZLII in a secondary role and emits a
manual-review queue for `probable` and `ambiguous` cases. `exact` matches are
treated as corroboration only, not canonical promotion.

## Operational Notes

- Use official metadata as the primary keying input.
- Keep NZLII-derived content outside canonical records until manually reviewed.
- Preserve retrieval timestamp and content hash for provenance.
- Treat `missing` and `out_of_scope` as non-review outputs unless upstream
  policy changes.
