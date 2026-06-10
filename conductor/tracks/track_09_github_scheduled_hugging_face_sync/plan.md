# Plan - GitHub Scheduled Hugging Face Sync

## Tasks
- [x] Confirm `.github/workflows/hf_sync.yml` exists on the default branch.
- [x] Configure GitHub secrets and variables from Track 02.
- [x] Run workflow manually with conservative inputs for the approved partial
  launch.
- [x] Confirm workflow uploads only changed content for the partial launch.
- [ ] Run workflow manually without `max_works` only after Track 07 and Track 08
  are proven.
- [ ] Confirm scheduled daily runs restore Hugging Face state before syncing.
- [ ] Confirm GitHub Actions summary includes sync state and latest changes over
  routine maintenance runs.

## Current blocker

- Manual live sync and no-change upload proof passed for the approved
  partial/API-discovery launch.
- The scheduled-run launch gate was explicitly waived by the repository owner on
  2026-06-09 after the first post-fix scheduled event did not dispatch.
- Full and recurring maintenance proof remains blocked until Tracks 04, 07, and
  08 establish a full seed and full validated corpus.
