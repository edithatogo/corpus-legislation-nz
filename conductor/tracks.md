# Project Tracks

This file tracks the major work items for `nz-legislation-corpus`.

---

## Status Key

- `todo`: not started.
- `blocked`: waiting on credentials, external access, or a decision.
- `ready`: prerequisites are available and implementation can proceed.
- `in_progress`: actively being worked.
- `done`: acceptance criteria are met and evidence is recorded.

## Track 01 - Repository Commit And Release Baseline

Status: `done`

Goal: get the current local implementation into a clean Git baseline before any live data operation is treated as repeatable.

Actions:

- Resolve the parent `OneDrive - Flinders` Git root lock issue or move `corpus-law-nz` into an isolated Git repository.
- Commit the currently staged rate-limit hardening, bootstrap guardrails, tests, and documentation.
- Generate a clean `uv.lock` from the final repository root.
- Switch CI dependency installation to `uv sync --all-extras --frozen` after `uv.lock` exists.
- Run `pytest -q -p no:cacheprovider tests`.
- Run `ruff check src/nz_legislation_corpus tests`.

Acceptance criteria:

- Git history contains a commit for the rate-limit work.
- `uv.lock` is committed.
- Tests and lint pass from the clean checkout.

Evidence to record:

- Commit SHA.
- Test command output summary.
- Lint command output summary.

## Track 02 - Credential And Secret Inventory

Status: `blocked`

Goal: confirm all credentials and GitHub variables required for live corpus operations are present, scoped correctly, and stored in the right place.

Actions:

- Confirm `NZ_LEGISLATION_API_KEY` exists and can call the NZ Legislation API.
- Confirm `HF_TOKEN` exists and has write access only to the intended Hugging Face dataset repository where possible.
- Confirm `HF_REPO_ID` is final.
- Confirm `ZENODO_TOKEN` exists for sandbox first.
- Decide whether production Zenodo uses a separate token and required reviewer environment.
- Store GitHub secrets: `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, and `ZENODO_TOKEN`.
- Store GitHub variables: `HF_REPO_ID`, `NZLC_SEARCH_TERMS`, `NZLC_SEARCH_FIELD`, `NZLC_SEARCH_SORT_BY`, `NZLC_LEGISLATION_TYPES`, `ARCHIVE_CREATORS_JSON`, and archive metadata.
- Run `uv run nzlc doctor` locally or through GitHub Actions.

Acceptance criteria:

- `nzlc doctor` passes without exposing secret values.
- GitHub Actions has the required secrets and variables.
- Zenodo production publication remains approval-gated.

Evidence to record:

- Redacted `nzlc doctor` result.
- GitHub repository variable names, not values.
- GitHub environment names and protection status.

## Track 03 - Hugging Face Dataset Shell

Status: `blocked`

Goal: create and verify the Hugging Face dataset repository before uploading corpus data.

Actions:

- Create or confirm the Hugging Face dataset repository named by `HF_REPO_ID`.
- Run `scripts/create_huggingface_dataset_repo.sh "$HF_REPO_ID"` or equivalent API setup.
- Confirm the remote layout is root-based, not nested under `data/`.
- Confirm `.gitattributes`, dataset card metadata, and lightweight root placeholders are correct.
- Remove any legacy `data/...` placeholders if present.

Acceptance criteria:

- Hugging Face repo exists and is writable by the configured token.
- Root-level layout is ready for `parquet/`, `raw_xml/`, `manifests/`, and `_state/`.
- Dataset card describes live corpus status without claiming full coverage before discovery proof.

Evidence to record:

- Hugging Face repo URL.
- Root layout listing.
- Dataset card revision or commit hash.

Current blocker:

- `HF_REPO_ID` is not configured in the local environment.
- `HF_TOKEN` is not configured in the local environment.
- Public search/open checks on 2026-06-07 did not confirm an existing public `edithatogo/nz-legislation-corpus` dataset shell.
- The repository shell cannot be created, confirmed writable, or inspected for layout until the final Hugging Face dataset ID and a write-capable token are supplied.

## Track 04 - Source Discovery Completeness

Status: `blocked`

Goal: establish the discovery method needed before the project can claim a complete corpus.

Actions:

- Contact or check the NZ Legislation source for an official work ID export or complete inventory.
- If no official export is available, build `seeds/work_ids.txt` from a documented authoritative inventory.
- Keep comments and provenance in the seed file or adjacent documentation.
- Reconcile seed coverage against search-based discovery.
- Define expected counts by legislation type, status, and year where available.
- Document any known exclusions, ephemeral IDs, or incorporated-by-reference caveats.

Acceptance criteria:

- `seeds/work_ids.txt` or an equivalent documented inventory exists.
- `docs/source_discovery_strategy.md` states the actual discovery source used.
- Public docs distinguish pipeline completeness from proven corpus completeness.

Evidence to record:

- Seed source.
- Work ID count.
- Reconciliation notes and unresolved gaps.

Current blocker:

- Public NZ Legislation API and developer documentation checked on 2026-06-07 describe search-oriented endpoints but did not identify a complete work-ID export or bulk inventory endpoint.
- No authoritative `seeds/work_ids.txt` exists in this repository.
- Public docs now distinguish API-first pipeline readiness from proven corpus completeness.

## Track 05 - Conservative Live Smoke Sync

Status: `blocked`

Goal: prove the live sync path against external services without risking rate limits or large uploads.

Actions:

- Set `NZLC_MIN_SECONDS_BETWEEN_REQUESTS=1.0`.
- Run `uv run nzlc sync --seed-work-ids seeds/work_ids.txt --max-works 5`.
- Run `uv run nzlc validate`.
- Run `uv run nzlc manifest`.
- Run `uv run nzlc coverage-report`.
- Inspect `data/_state/sync_state.json`, `data/manifests/latest_manifest.json`, and `data/manifests/latest_changes.json`.

Acceptance criteria:

- Five or fewer seed works are synced exactly as requested.
- Validation passes.
- Manifest and coverage report are generated.
- No rate-limit failures are unhandled.

Evidence to record:

- Command summaries.
- Synced work count.
- Any API warnings from sync state.

Current blocker:

- `NZ_LEGISLATION_API_KEY` is not configured in the local environment.
- `seeds/work_ids.txt` does not exist; only example seed files are present.
- No live smoke sync was run because it would fail before proving the intended external API path.

## Track 06 - First Hugging Face Smoke Upload

Status: `blocked`

Goal: prove upload, restore, and no-change behavior on Hugging Face with the small smoke corpus.

Actions:

- Run `uv run nzlc hf-upload` against the smoke data.
- Download the Hugging Face dataset back into a clean local `data/` directory.
- Confirm root-level remote files map to local `data/parquet/`, `data/raw_xml/`, `data/manifests/`, and `data/_state/`.
- Rerun upload with unchanged content and confirm it skips or produces no content churn.
- Inspect the Hugging Face dataset viewer and sample Parquet reads.

Acceptance criteria:

- Smoke corpus is visible in Hugging Face.
- Re-download produces the expected local layout.
- No-change upload behavior is proven.

Evidence to record:

- Hugging Face commit or revision.
- Manifest hash before and after no-change upload.
- Sample Parquet read result.

Current blocker:

- `HF_TOKEN` and `HF_REPO_ID` are not configured in the local environment.
- `data/` is absent, so there is no smoke corpus or manifest to upload.
- Track 05 has not produced a conservative live smoke corpus yet.

## Track 07 - Full Corpus Bootstrap Download

Status: `blocked`

Goal: download the full corpus into local `data/` using the proven discovery method and conservative pacing.

Actions:

- Confirm enough local disk space for raw files, Parquet, manifests, and temporary archive work.
- Restore current Hugging Face corpus state into `data/` if any previous upload exists.
- Run full seed sync with `NZLC_MIN_SECONDS_BETWEEN_REQUESTS` set conservatively.
- Use staged batches if the seed inventory is large or API limits are uncertain.
- Preserve sync state after each batch.
- Run `uv run nzlc validate`, `uv run nzlc manifest`, and `uv run nzlc coverage-report`.
- Review missing text, missing XML URLs, failed versions, and ephemeral identifiers.

Acceptance criteria:

- All seed works are attempted.
- Failed versions are recorded and triaged.
- Validation passes or documented exceptions are accepted.
- Coverage report is reviewed before any public completeness claim.

Evidence to record:

- Total works attempted.
- Total versions and records produced.
- Failed or skipped version list.
- Final manifest hash.
- Coverage report path.

Current blocker:

- `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, and `HF_REPO_ID` are not configured in the local environment.
- `seeds/work_ids.txt` does not exist, so there is no proven full-corpus seed inventory to attempt.
- `data/` is absent, and Tracks 05 and 06 have not produced or uploaded a smoke corpus.
- Local `C:` free space checked on 2026-06-07: 19,907,948,544 bytes free; final adequacy cannot be confirmed until expected corpus/archive size is known.

## Track 08 - Full Hugging Face Corpus Upload

Status: `blocked`

Goal: publish the full validated corpus to Hugging Face as the live operational dataset.

Actions:

- Confirm `HF_XET_HIGH_PERFORMANCE=1` for the upload environment.
- Run `uv run nzlc hf-upload`.
- Use resumable upload behavior if the upload is interrupted.
- Verify Hugging Face contains `parquet/`, `raw_xml/`, `records.jsonl`, `manifests/`, and `_state/` as expected.
- Re-download the dataset into a clean location and compare manifest hashes.
- Confirm the dataset card states the discovery and coverage status accurately.

Acceptance criteria:

- Full corpus upload completes.
- Re-downloaded manifest matches the uploaded manifest.
- Dataset card and README do not overclaim completeness.

Evidence to record:

- Hugging Face revision or commit hash.
- Uploaded size.
- Manifest hash.
- Re-download verification result.

Current blocker:

- `HF_TOKEN`, `HF_REPO_ID`, and `HF_XET_HIGH_PERFORMANCE` are not configured in the local environment.
- `data/`, `data/manifests/latest_manifest.json`, and `data/parquet/` are absent, so there is no full validated corpus to upload.
- Track 07 has not produced the full bootstrap corpus yet.
- The upload helper defaults `HF_XET_HIGH_PERFORMANCE=1` during upload, but no upload was attempted because required credentials and corpus data are absent.

## Track 09 - GitHub Scheduled Hugging Face Sync

Status: `blocked`

Goal: make GitHub Actions the normal maintenance loop for the Hugging Face live corpus.

Actions:

- Confirm `.github/workflows/hf_sync.yml` exists on the default branch.
- Configure GitHub secrets and variables from Track 02.
- Run workflow manually with `max_works=5` and `min_seconds_between_requests=1.0`.
- Run workflow manually without `max_works` only after Track 07 and Track 08 are proven.
- Confirm scheduled daily runs restore Hugging Face state before syncing.
- Confirm workflow uploads only changed content.
- Confirm GitHub Actions summary includes sync state and latest changes.

Acceptance criteria:

- Manual smoke workflow passes.
- Full manual workflow passes.
- Daily scheduled workflow is enabled and uses the Hugging Face repo as the live data hub.

Evidence to record:

- GitHub Actions run URLs.
- Workflow inputs used.
- Latest successful scheduled run URL.

Current blocker:

- `.github/workflows/hf_sync.yml` exists locally and includes schedule, manual dispatch inputs, Hugging Face restore, sync, upload, and step-summary sections.
- No Git remote is configured, so there is no target GitHub repository/default branch to inspect or dispatch.
- `GITHUB_REPOSITORY`, `GH_TOKEN`, `NZ_LEGISLATION_API_KEY`, `HF_TOKEN`, and `HF_REPO_ID` are not configured in the local environment.
- Tracks 02, 05, 07, and 08 remain blocked, so the workflow cannot yet prove smoke, full, scheduled, or no-change behavior.

## Track 10 - Maintenance Doctor And Alerting

Status: `blocked`

Goal: surface token, API, and dependency failures before they affect the live corpus.

Actions:

- Enable `.github/workflows/doctor.yml`.
- Confirm doctor runs without mutating corpus data.
- Confirm GitHub Actions notifications reach the maintainer.
- Decide whether to add a lightweight webhook or issue creation on repeated failures.
- Review Dependabot configuration and security workflows.

Acceptance criteria:

- Doctor workflow passes once with live secrets.
- Failure notification path is known.
- Maintainer has a weekly check routine.

Evidence to record:

- Doctor workflow run URL.
- Notification destination.
- Any follow-up alerting issue.

Current blocker:

- `.github/workflows/doctor.yml` exists locally and is scheduled weekly, but no Git remote is configured, so it cannot be confirmed enabled on the default branch.
- Local non-network `uv run --no-cache nzlc doctor` runs without creating `data/`, but live network doctor cannot pass until Track 02 secrets and variables are configured.
- Dependabot, CodeQL, and OpenSSF Scorecard configurations exist locally.
- GitHub Actions notification delivery cannot be confirmed until the repository exists and a workflow run has completed.

## Track 11 - Monthly Full Reconciliation

Status: `blocked`

Goal: keep the corpus complete over time, not only during the first bootstrap.

Actions:

- Define a monthly or quarterly full reconciliation cadence.
- Compare seed inventory, search discovery, and coverage report outputs.
- Add newly discovered work IDs to `seeds/work_ids.txt` with provenance.
- Rerun full sync in staged batches when the seed file changes materially.
- Review counts by legislation type, status, and year.

Acceptance criteria:

- Reconciliation cadence is documented.
- Seed changes are reviewed.
- Coverage deltas are explained in `latest_changes.json` or a maintenance note.

Evidence to record:

- Reconciliation date.
- Added or removed work IDs.
- Coverage deltas.

Current blocker:

- `docs/reconciliation_runbook.md` now documents the monthly cadence and procedure.
- `seeds/work_ids.txt` is absent, so seed changes cannot be reviewed or applied.
- `data/manifests/coverage_report.json` is absent, so coverage deltas cannot be compared.
- Tracks 04, 07, 08, and 09 remain blocked, so no full corpus or scheduled maintenance loop exists yet to reconcile.

## Track 12 - Zenodo Sandbox Archive

Status: `blocked`

Goal: prove annual immutable archiving without publishing to production.

Actions:

- Set Zenodo sandbox token and sandbox API URL.
- Run `uv run nzlc archive --year <year> --output-dir dist/archive`.
- Run `uv run nzlc zenodo-upload --year <year> --archive-dir dist/archive` against sandbox.
- Verify archive manifest and checksums.
- Verify duplicate-file replacement behavior if rerun.

Acceptance criteria:

- Sandbox draft is created or updated.
- Archive, manifest, and checksum files are present.
- No production publication occurs.

Evidence to record:

- Sandbox deposition URL.
- Archive filename and checksum.
- Workflow run URL if performed in GitHub Actions.

Current blocker:

- `ZENODO_TOKEN`, `ZENODO_API_URL`, `ARCHIVE_CREATORS_JSON`, and `HF_REPO_ID` are not configured in the local environment.
- `data/` is absent, so there is no corpus available to archive.
- `dist/archive` is absent, so there are no archive, manifest, or checksum files to upload.
- The Zenodo client deletes duplicate-named draft files before upload, but duplicate replacement cannot be verified without a sandbox draft and token.

## Track 13 - Protected Production Zenodo Archive

Status: `blocked`

Goal: publish annual DOI snapshots only after explicit approval.

Actions:

- Configure `zenodo-production` GitHub environment with required reviewers.
- Confirm production `ZENODO_TOKEN` is environment-scoped.
- Run annual workflow with `publish=false` first.
- Review production draft metadata, license, creators, related identifiers, and files.
- Publish only after reviewer approval and explicit `publish=true`.
- Record DOI in `CITATION.cff`, `DATASET_CARD.md`, and Hugging Face dataset card.

Acceptance criteria:

- Production draft path is proven.
- Publication requires approval.
- DOI is recorded after publication.

Evidence to record:

- Production deposition URL.
- DOI.
- Commit updating citation files.

Current blocker:

- No Git remote is configured, so the `zenodo-production` GitHub environment and required reviewers cannot be verified live.
- `ZENODO_TOKEN`, `ZENODO_API_URL`, `ZENODO_DEPOSITION_ID`, `ARCHIVE_CREATORS_JSON`, `GITHUB_REPOSITORY`, `GH_TOKEN`, and `HF_REPO_ID` are not configured in the local environment.
- Track 12 sandbox archive has not passed, so production archive work must not proceed.
- `.github/workflows/annual_zenodo_archive.yml` routes production draft/publication runs through `zenodo-production` and keeps `publish=false` by default, but no production draft or DOI exists yet.

## Track 14 - Legal, Citation, And Dataset Wording

Status: `blocked`

Goal: keep public statements accurate about corpus coverage, licensing, and incorporated-by-reference material.

Actions:

- Review `README.md`, `DATASET_CARD.md`, `CITATION.cff`, and archive metadata.
- State whether discovery is complete, partial, seed-based, or search-based.
- Separate code license from legislation reuse status.
- Add caveats for incorporated-by-reference material and non-legislative website content.
- Confirm citation guidance for Hugging Face live data and Zenodo annual snapshots.

Acceptance criteria:

- Public docs make no unsupported completeness claim.
- License and citation wording are internally consistent.
- Zenodo and Hugging Face metadata align.

Evidence to record:

- Reviewed files.
- Reviewer notes.
- Metadata commit SHA.

Current blocker:

- Reviewed `README.md`, `DATASET_CARD.md`, `CITATION.cff`, and Hugging Face dataset-card generation in `scripts/init_huggingface_dataset.py`.
- Public wording now states coverage is not proven complete, separates code licensing from source-content reuse status, and distinguishes live Hugging Face citation from fixed Zenodo citation.
- Official NZ Legislation copyright/disclosure pages checked on 2026-06-07 support Crown copyright / Creative Commons attribution wording, with separate caution retained for third-party or non-legislative material.
- Track remains blocked for final metadata commit SHA because the broader Conductor changes are not committed yet and live Hugging Face/Zenodo metadata cannot be verified.

## Track 15 - Downstream Researcher Usability

Status: `blocked`

Goal: make the published corpus easy to inspect and query after the live hub is stable.

Actions:

- Add a small public sample split if useful for users who do not want the full corpus.
- Add DuckDB or Polars examples that query Parquet directly from Hugging Face.
- Add a minimal data dictionary from schema fields.
- Optionally add a Hugging Face Space for browsing/search after core maintenance is stable.

Acceptance criteria:

- A new user can query the Parquet dataset without downloading the full raw corpus.
- Examples are tested or manually verified.
- Optional browser UI is clearly secondary to the dataset pipeline.

Evidence to record:

- Example command output.
- Sample dataset path or revision.
- Documentation links.

Current blocker:

- Added `docs/researcher_quickstart.md` with DuckDB `hf://` examples, local PyArrow examples, and sample split policy.
- Added `docs/data_dictionary.md` from `schemas/legislation_record.schema.json`.
- `README.md` and `DATASET_CARD.md` now link to downstream researcher documentation.
- Live Hugging Face query output, sample dataset path/revision, and optional browser UI remain blocked until Tracks 03 and 08 publish the dataset.

## Track 16 - GitHub Repository Hardening

Status: `blocked`

Goal: make the GitHub repository safe to operate as the automation controller for the live Hugging Face corpus.

Actions:

- Create or confirm the final GitHub repository. Blocked: no Git remote is configured.
- Push the code-only repository without `data/`, `dist/`, cache directories, or generated corpus files. Blocked until the final GitHub repository exists.
- Enable branch protection on the default branch. Blocked until the final GitHub repository exists.
- Require the tests workflow before merge once CI is stable. Blocked until branch protection/rulesets can be applied on GitHub.
- Enable secret scanning and push protection where available. Blocked until GitHub repository settings are available.
- Enable Dependabot alerts and dependency update PRs. Dependency update PR configuration is present in `.github/dependabot.yml`; live alert enablement is scripted but blocked until GitHub repository settings are available.
- Confirm `CODEOWNERS`, issue templates, pull request template, security policy, and contribution docs are present if the repo is public. Done locally.
- Confirm workflows have minimum permissions and do not expose secrets in logs. Done locally.

Acceptance criteria:

- Default branch is protected.
- Tests are required for code changes.
- Secret scanning and dependency alerts are enabled or explicitly documented as unavailable.
- Repository remains code-only.

Evidence to record:

- GitHub repository URL.
- Branch protection summary.
- Enabled security settings.
- First passing CI run URL.

Current evidence:

- No Git remote is configured, so the final GitHub repository URL, branch protection summary, enabled security settings, and CI run URL cannot be recorded yet.
- GitHub repository URL: `https://github.com/edithatogo/nz-legislation-corpus-pipeline`.
- Branch protection summary: `main` requires strict `tests`, one approving review, admin enforcement, linear history, no force pushes, and no deletions.
- Enabled security settings: Dependabot security updates, secret scanning, and push protection.
- First passing CI run: baseline `Tests` run `27087158077` and `CodeQL` run `27087158073` passed on 2026-06-07.
- Remaining blocker: Scorecard workflow fix must be merged through branch protection before the next Scorecard run can pass.
- `.gitignore` excludes generated corpus/archive/cache paths including `data/`, `dist/`, `.hf_cache/`, and `.track15-smoke/`; no tracked files exist under generated corpus/archive paths.
- `SECURITY.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS`, pull request template, issue templates, Dependabot config, CodeQL, Scorecard, tests, doctor, Hugging Face sync, and annual Zenodo workflows are present.
- Workflow permissions are minimum-scoped for local review: `contents: read` by default, with `security-events: write` only where `codeql.yml` and `scorecard.yml` upload SARIF.

## Track 17 - Runtime Capacity, Batching, And Resume

Status: `blocked`

Goal: make the full corpus bootstrap and recurring sync practical under local disk, GitHub Actions runtime, API rate limits, and upload interruption constraints.

Actions:

- Estimate disk required for raw files, normalized records, Parquet, manifests, and annual archive staging. Done in `docs/runtime_capacity_runbook.md`.
- Decide whether first full bootstrap runs locally, on GitHub Actions, or on another controlled runner. Done: first full bootstrap should run on a controlled local or self-hosted runner.
- Define batch size and pacing defaults for first full sync. Done in `docs/runtime_capacity_runbook.md`.
- Confirm sync state is preserved between batches. Done with `tests/test_sync_resume.py`.
- Confirm interrupted Hugging Face uploads can resume without corrupting the remote dataset. Blocked until `HF_TOKEN`, `HF_REPO_ID`, and a live dataset are available.
- Add an operator note for cleaning local generated data safely after upload and verification. Done in `docs/runtime_capacity_runbook.md`.
- Record the fallback plan if the full bootstrap exceeds GitHub Actions timeout. Done in `docs/runtime_capacity_runbook.md`.

Acceptance criteria:

- Bootstrap runner and disk budget are documented.
- Batch/resume procedure is written and tested with a non-trivial batch.
- Generated local data cleanup is documented and does not affect Git-tracked files.

Evidence to record:

- Disk estimate.
- Chosen runner.
- Batch size and pacing values.
- Resume test result.

Current evidence:

- Disk estimate documented in `docs/runtime_capacity_runbook.md`: reserve at least 25 GB free for the expected 6 GB class corpus, preferably 50 GB when archive staging or embeddings share the runner.
- Chosen runner documented: controlled local or self-hosted first bootstrap, then GitHub Actions for daily/latest maintenance after first verified upload.
- Batch defaults documented: 5-work smoke at 1.0 seconds pacing, 50-work pilot at 1.0 seconds, 250-work seed chunks at 0.5 seconds, and 500-1000 work chunks at 0.2 seconds only after throttle-free earlier batches.
- Resume behavior tested locally in `tests/test_sync_resume.py`; live Hugging Face interrupted-upload proof remains blocked until `HF_TOKEN`, `HF_REPO_ID`, and a live dataset are available.

## Track 18 - Data Quality And Schema Governance

Status: `blocked`

Goal: prevent silent schema drift or degraded corpus quality after the first public upload.

Actions:

- Define minimum validation checks required before upload. Done.
- Define which validation warnings block upload and which are informational. Done.
- Add or confirm fixture coverage for representative XML, HTML, missing-text, missing-format, and ephemeral-ID cases. Done.
- Version the record schema explicitly before public release. Done: `record_schema_version = "1.0"`.
- Document how schema changes are migrated or announced. Done in `docs/schema_governance.md`.
- Track data-quality metrics from `coverage_report.json` over time. Done via `data/manifests/coverage_history.jsonl`.

Acceptance criteria:

- Upload cannot proceed after blocking validation failures.
- Schema version is visible in records or manifests.
- Coverage metrics can be compared between runs.
- Public docs explain backward compatibility expectations.

Evidence to record:

- Schema version.
- Validation report path.
- Fixture list.
- Coverage baseline.

Current evidence:

- Schema version: `record_schema_version = "1.0"`.
- Validation report path: `data/manifests/validation_report.json`.
- Fixture list: `tests/fixtures/sample_legislation.xml`, `tests/fixtures/sample_legislation.html`, plus validation tests for missing text, missing XML URL, missing source format/metadata-only content, and ephemeral identifiers.
- Coverage metrics are written to `data/manifests/coverage_report.json` and appended to `data/manifests/coverage_history.jsonl`.
- Live coverage baseline remains blocked until Track 07/08 produce and publish the real corpus.

## Track 19 - Public Launch Decision

Status: `blocked`

Goal: make a deliberate launch decision after the corpus, automation, metadata, and maintenance loop are all proven.

Actions:

- Confirm Tracks 01 through 14 are done or explicitly waived. Blocked: Tracks 02-14 still have unresolved blockers.
- Confirm Hugging Face contains the full intended live corpus or clearly labels the dataset as partial. Blocked until Track 03/08 publish or confirm the live dataset.
- Confirm GitHub scheduled sync is enabled and has passed after the first upload. Blocked until Track 09 runs on a configured GitHub repository.
- Confirm Zenodo sandbox archive has passed. Blocked until Track 12 passes.
- Confirm public README, dataset card, and citation files match the actual coverage state. Done for current prelaunch state.
- Create a release note summarizing coverage, caveats, update cadence, and archival plan. Done as draft template.

Acceptance criteria:

- Public users can find the live dataset, source repository, coverage statement, and citation instructions.
- No public page claims full coverage unless Track 04 is proven.
- Maintainer has a clear monthly and annual operating checklist.

Evidence to record:

- Launch date.
- Hugging Face revision.
- GitHub release or tag.
- Final launch checklist.

Current evidence:

- Launch date: not assigned; current decision is `do not launch yet`.
- Hugging Face revision: blocked until the live dataset is published or verified.
- GitHub release or tag: blocked until a release/tag is created in `https://github.com/edithatogo/nz-legislation-corpus-pipeline`.
- Final launch checklist: `docs/public_launch_decision.md`.
- Draft release note: `docs/public_launch_release_note.md`.
- Tracking issues: #10 through #15 in `edithatogo/nz-legislation-corpus-pipeline`.
