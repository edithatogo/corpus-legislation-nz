## What changed

-

## Checks

- [ ] `uv run pytest -q`
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run ty check src tests scripts`
- [ ] `uv run python scripts/check_version_consistency.py`
- [ ] `uv run python scripts/check_artifact_provenance.py`
- [ ] `typos`, `taplo fmt --check pyproject.toml`, and `actionlint`
- [ ] Smoke fixture still passes
- [ ] No corpus data, tokens, caches, or local `.env` files committed

## Data/publication impact

- [ ] No Hugging Face upload impact
- [ ] No Zenodo publication impact
- [ ] Licensing/citation text reviewed if relevant
