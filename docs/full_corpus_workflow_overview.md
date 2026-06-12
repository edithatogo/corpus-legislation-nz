# Full Corpus Workflow Overview

This repo now has a complete workflow tree for the full-corpus maintenance lane.
The intent is to keep the target boundaries explicit and the execution host
appropriate for each step.

For step-by-step run inputs and review artifacts, see
`docs/full_corpus_operations.md`.

## Sequence

1. Initialize the historical Hugging Face shell with
   `.github/workflows/init_historical_hf_shell.yml`.
2. Build or review the full corpus bootstrap with
   `.github/workflows/full_corpus_bootstrap.yml`.
3. Review and upload the validated full corpus with
   `.github/workflows/full_corpus_hf_upload.yml`.
4. Reconcile seed and coverage drift over time with
   `.github/workflows/monthly_full_reconciliation.yml`.

## Historical branch

Historical corpus work stays separate from the full-corpus lane:

- Use `.github/workflows/historical_batch_review.yml` for parallel no-upload
  review of historical batches on GitHub-hosted runners.
- Use `.github/workflows/historical_hf_upload.yml` for the confirmed historical
  publish path.

## Host boundaries

- First full bootstrap: controlled local or self-hosted runner.
- Historical review fan-out: GitHub-hosted runners.
- Confirmed Hugging Face publish steps: serial workflow execution.

## Guardrails

- The historical dataset shell must be separate from the live partial dataset.
- Historical publication must fail closed if `HF_HISTORICAL_REPO_ID` is absent
  or equals `HF_REPO_ID`.
- Public wording must not claim full coverage until the seed inventory is
  reconciled and reviewed.
