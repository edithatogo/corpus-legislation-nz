# Schema governance

The public record schema is versioned as `record_schema_version = "1.0"`.

## Blocking validation failures

The following validation findings block upload:

- duplicate `stable_id`
- duplicate `version_id`
- missing required fields
- empty `text`, unless a fixture or explicit metadata-only test passes `--allow-empty-text`
- `text_sha256` mismatch
- JSON Schema validation errors
- `record_schema_version` mismatch

`nzlc hf-upload` runs validation before upload and writes `data/manifests/validation_report.json`. If the report contains errors, upload stops.

## Informational warnings

The following findings are warnings, not upload blockers:

- missing XML URL when another source format is available
- ephemeral identifiers flagged with `id_is_ephemeral`

Warnings must be reviewed in `validation_report.json` and `coverage_report.json` before public claims about completeness or stability.

## Fixture coverage

The test suite covers:

- representative XML extraction and validation: `tests/fixtures/sample_legislation.xml`
- representative HTML extraction and validation: `tests/fixtures/sample_legislation.html`
- missing text as a blocking validation error
- missing XML URL as an informational warning
- missing source format with empty text as a blocking validation error
- ephemeral IDs as informational warnings and coverage metrics

## Schema changes

Backward-compatible additions may keep `record_schema_version = "1.0"` only when existing records remain valid and public field meanings do not change.

Breaking changes require:

1. incrementing `RECORD_SCHEMA_VERSION` in `src/nz_legislation_corpus/schema.py`;
2. updating `schemas/legislation_record.schema.json`;
3. adding or updating migration notes in this document;
4. updating `docs/data_dictionary.md`;
5. recording the change in the Hugging Face dataset card and release notes before publication.

Do not silently repurpose an existing field. Add a new field, deprecate the old field in documentation, and keep both through at least one public release cycle where possible.

## Coverage history

`nzlc coverage-report` writes the current report to `data/manifests/coverage_report.json` and appends the same metrics to `data/manifests/coverage_history.jsonl`.

Compare consecutive history rows for:

- total record count;
- counts by legislation type, status, and year;
- missing text records;
- missing XML URL records;
- ephemeral identifier records.

Large unexpected movement in these metrics should be treated as a release blocker until explained.

## Period quality reviews

When a full-bootstrap or period-bootstrap artifact includes
`generated/full-corpus-periods/period_context.json`,
`nzlc review-full-corpus-bootstrap` emits a `period_quality` object in the
review report. It repeats the period identifier, source work-ID count, produced
record count, validation status, manifest hash, failed-version count, the same
missing text, missing XML URL, and ephemeral identifier risk indicators used by
full-corpus coverage, and direct `ok`/`triage_required` handoff flags.

Period review artifacts are quality slices, not independent completeness
claims. Treat any non-zero failed-version count, missing text count, missing XML
URL count, ephemeral identifier count, or count mismatch as a triage item before
using that period as handoff evidence.
