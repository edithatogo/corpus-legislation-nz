# CI, code quality, and security tooling

Track 32 makes the local and CI quality surface explicit. Publication workflows
remain separate: these checks do not upload to Hugging Face, publish Zenodo
records, create releases, or mutate dataset manifests.

## Blocking local checks

Run these before merging normal code changes:

```powershell
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run ty check src tests scripts
uv run python scripts\check_version_consistency.py
typos
taplo fmt --check pyproject.toml
actionlint
```

`ty` is configured with `[tool.ty.rules] all = "error"` and checks packaged
modules, tests, and repository scripts. The `scripts` directory is importable so
test modules can exercise maintenance scripts under the same type-checking
rules as application code.

## CI adoption

`.github/workflows/code_quality.yml` adds:

- `uv sync --extra dev --frozen`;
- `ruff check .`;
- `ruff format --check .`;
- `ty check src tests scripts`;
- `scripts/check_version_consistency.py`;
- `crate-ci/typos`;
- `taplo fmt --check pyproject.toml`;
- `raven-actions/actionlint` for workflow syntax/expression linting, with
  ShellCheck style lint disabled in CI so existing shell-summary style does not
  block this track;
- advisory `zizmor` workflow security audit with nonzero findings tolerated
  until the workflow-hardening backlog is complete.

The workflow uses `permissions: contents: read` and `persist-credentials:
false` on checkout. It has no secrets and no publication permissions.

## Security-tooling decisions

| Tool | Decision | Notes |
| --- | --- | --- |
| `uv` | Adopted, blocking | Frozen dependency install remains required. |
| `ruff` | Adopted, blocking | Lint and format checks are enforced. |
| `ty` | Adopted, blocking | Strict baseline is now green for `src`, `tests`, and `scripts`. |
| `typos` | Adopted, blocking | Local `typos` passed for the current repository. |
| `taplo` | Adopted, blocking for `pyproject.toml` | TOML formatting is checked after applying Taplo formatting to `pyproject.toml`. |
| `actionlint` | Adopted, blocking for workflow syntax | Found and drove the fix for the historical upload workflow's 12-input `workflow_dispatch` shape. CI disables ShellCheck style lint for now. |
| `zizmor` | Adopted, advisory | Current findings include unpinned action references and template-expansion risks in publication and historical workflows. These are recorded as security-hardening backlog before a blocking gate is safe. |
| CodeQL | Adopted | Existing `.github/workflows/codeql.yml` remains the SARIF-producing code scanning workflow. |
| OpenSSF Scorecard | Adopted | Existing `.github/workflows/scorecard.yml` remains scheduled/manual and keeps `publish_results: false`. |
| Renovate | Adopted | Routine dependency updates are configured in `renovate.json`; no automerge. |
| pre-commit | Adopted locally | `.pre-commit-config.yaml` runs Ruff and Ruff format. CI remains authoritative. |

## Zizmor backlog

The current offline `zizmor --no-online-audits .github\workflows` baseline is
not clean. The main classes are:

- unpinned action references in existing workflows;
- checkout steps without `persist-credentials: false`;
- direct `${{ inputs.* }}` template expansion inside shell `run` blocks.

Those findings should be addressed in a dedicated workflow-hardening pass. Until
then, the CI `zizmor` job is advisory with `continue-on-error: true`, so the
repository gets evidence without blocking unrelated corpus work.

## Publication gate boundary

Dependency-update PRs and quality workflows cannot publish datasets or archives.
Hugging Face and Zenodo remain gated through their separate manual/protected
workflows and release evidence requirements.
