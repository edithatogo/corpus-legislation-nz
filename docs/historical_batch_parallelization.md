# Historical Batch Parallelization

The historical corpus can be reviewed batch-by-batch on GitHub Actions
using GitHub-hosted runners, without using the laptop as the execution host.

Use the manual workflow:

`.github/workflows/historical_batch_review.yml`

It fans out reviewed seed batches across multiple GitHub-hosted runners, keeps
each batch isolated, and uploads batch-level review artifacts for later
inspection. The workflow is for review and sync evidence only; it does not
perform the confirmed Hugging Face publish step.

Suggested usage:

```text
seed_batch_ids_csv=0005,0006,0007
merge_policy=restore_merge
max_parallel=3
max_works=none
```

This approach is safe because each batch job restores from the historical
dataset, syncs against its own reviewed seed file, and writes only to its own
runner workspace and GitHub artifact bundle. The existing serial
`historical_hf_upload.yml` workflow remains the confirmed-upload path.
