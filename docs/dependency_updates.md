# Dependency updates

This repository uses Renovate for routine dependency update pull requests.

Renovate is configured in `renovate.json` to manage:

- GitHub Actions workflow actions;
- PEP 621 dependencies in `pyproject.toml`, with `uv.lock` maintenance;
- pre-commit hook versions.

Dependabot version-update configuration has been removed to avoid duplicate
dependency PR streams. GitHub security alerts can remain enabled separately in
repository settings.

Renovate PRs are intentionally conservative:

- no automerge;
- lockfile-first updates so package minimum constraints are not raised without
  review;
- low-risk minor and patch updates are grouped;
- major updates remain separate;
- optional embedding dependencies are grouped separately because they can pull
  large ML stacks;
- dependency updates must not upload to Hugging Face or publish to Zenodo.

The release/versioning gate is separate from dependency updates. Renovate PRs
may run tests, lint, and `uv run python scripts/check_version_consistency.py`,
but they must not create GitHub releases, upload Hugging Face datasets, publish
Zenodo records, or update manifest evidence except through an explicitly
reviewed release or corpus-maintenance track.
