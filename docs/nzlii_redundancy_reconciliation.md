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

The source inventory emitted by `nzlc nzlii-source-inventory` includes
`schema_version`, `source_role`, `coverage_warning`, and `sources[]` entries with
`collection`, `url_pattern`, `role`, `access_policy`, `canonical_status`, and
`caveat`. The initial inventory is deliberately limited to the NZLII New Zealand
Acts and New Zealand Regulations entry points used for Track 39 redundancy
planning.

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

The report also embeds a small NZLII source inventory and can compare candidate
matches against a seed work-ID file plus bootstrap-failure JSONL. Failed official
records with exact or probable NZLII candidates are surfaced for manual review;
they are not promoted automatically.

When `--bootstrap-failures-path` is supplied, the report adds
`text_rescue_triage_candidates` for failed official records that have an exact or
probable NZLII candidate. Each triage row records:

- `fallback_status`
- `source_role`
- `retrieval_method`
- `canonical_promotion_allowed`
- `review_required`
- the selected NZLII candidate provenance

These rows are review evidence only. `canonical_promotion_allowed` is always
`false` for this Track 39 output, even when the candidate is classified as
`exact`.

NZLII-derived evidence must carry its source-specific rights note into sync
state, review reports, manifests, and public-facing metadata when it is used for
triage or rescue. It must not be treated as a blanket relicensing of upstream
text, and it must not be used to claim corpus completeness before the official
inventory and reconciliation evidence support that claim.

## Operational Notes

- Use official metadata as the primary keying input.
- Keep NZLII-derived content outside canonical records until manually reviewed.
- Preserve retrieval timestamp and content hash for provenance.
- Treat `missing` and `out_of_scope` as non-review outputs unless upstream
  policy changes.
- `nzlc nzlii-source-inventory` writes the documented source inventory and
  caveats as JSON.
- `nzlc reconcile-nzlii --bootstrap-failures-path ...` writes text-rescue
  triage candidates without fetching NZLII pages or modifying canonical records.
