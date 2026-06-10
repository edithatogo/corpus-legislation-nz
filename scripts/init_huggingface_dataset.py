#!/usr/bin/env python3
"""Create and initialise the Hugging Face Dataset repo used by this pipeline.

This is intentionally safe and idempotent. It creates the dataset repository if it
is missing, then uploads lightweight repository metadata only. It does not upload
corpus data; the GitHub Actions sync workflow owns data publication.
"""

from __future__ import annotations

import os
import sys
from contextlib import suppress
from datetime import UTC, datetime
from textwrap import dedent

from huggingface_hub import HfApi


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    repo_id = os.getenv("HF_REPO_ID") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not repo_id or "/" not in repo_id:
        raise SystemExit(
            "Usage: HF_TOKEN=... HF_REPO_ID=namespace/name scripts/init_huggingface_dataset.py"
        )

    token = required_env("HF_TOKEN")
    private = env_bool("HF_PRIVATE", default=False)
    pretty_name = os.getenv("HF_DATASET_PRETTY_NAME", "New Zealand Legislation Corpus")
    source_repo = os.getenv(
        "GITHUB_REPO_URL", "https://github.com/edithatogo/corpus-legislation-nz"
    )
    zenodo_placeholder = os.getenv("ZENODO_CONCEPT_DOI", "TBD after first annual snapshot")
    created_at = datetime.now(UTC).isoformat()

    api = HfApi(token=token)
    repo_url = api.create_repo(repo_id=repo_id, repo_type="dataset", private=private, exist_ok=True)

    readme = dedent(f"""\
    ---
    pretty_name: {pretty_name}
    language:
    - en
    tags:
    - law
    - legislation
    - new-zealand
    - corpus
    - legal-nlp
    - parquet
    - xet
    - open-data
    size_categories:
    - 1M<n<10M
    license: other
    ---

    # {pretty_name}

    This dataset repository is the live operational home for an evolving New Zealand legislation corpus pipeline. Coverage is not proven complete until reconciled against an authoritative inventory.

    It is intended to be populated by the `corpus-legislation-nz` GitHub Actions workflow, which uses the official New Zealand Legislation API, validates and normalizes records, writes stable partitioned Parquet, and publishes annual DOI-backed archival snapshots to Zenodo.

    ## Current status

    Repository shell initialised on `{created_at}`.

    The first real data upload should be performed by the GitHub Actions workflow after the following are configured in the GitHub source repository:

    - `NZ_LEGISLATION_API_KEY`
    - `HF_TOKEN`
    - `ZENODO_TOKEN`
    - `HF_REPO_ID={repo_id}`

    ## Expected layout

    ```text
    parquet/
      legislation_type=<type>/year=<year>/part-00000.parquet
    raw_xml/
    manifests/
      latest_manifest.json
      latest_changes.json
    _state/
      sync_state.json
    ```

    ## Storage strategy

    This repository is designed for Hugging Face Hub's Xet-backed storage. The pipeline writes stable Parquet partitions and avoids unnecessary rewrites so unchanged chunks can be deduplicated efficiently.

    ## Source pipeline

    Source repository: {source_repo}

    ## Citation and archiving

    This live repository may change over time. For live use, cite this Hugging Face dataset URL, access date, and the manifest hash. For formal academic or fixed-version citation, cite the annual Zenodo snapshot once published.

    Annual Zenodo DOI: {zenodo_placeholder}

    ## Legal and licensing caveat

    The source repository code is licensed separately. This dataset card does not relicense legislation text or third-party source material. Check the official New Zealand Legislation copyright page for Crown copyright and attribution terms. Incorporated-by-reference materials, third-party content, agency website text, logos, emblems, and non-legislative linked resources may have separate rights or restrictions. Verify licensing and source terms before downstream redistribution or commercial use.

    ## Maintainer notes

    This repository should not be edited manually during normal operation. Prefer updating the GitHub pipeline and letting the workflow publish validated changes.
    """)

    gitattributes = dedent("""\
    *.parquet filter=lfs diff=lfs merge=lfs -text
    *.zst filter=lfs diff=lfs merge=lfs -text
    *.tar filter=lfs diff=lfs merge=lfs -text
    *.xml text eol=lf
    *.json text eol=lf
    *.jsonl text eol=lf
    *.md text eol=lf
    """)

    dataset_infos = dedent(f"""\
    {{
      "{repo_id.split("/")[-1]}": {{
        "description": "Live New Zealand legislation corpus pipeline maintained by an automated API-first workflow. Coverage is not proven complete until reconciled against an authoritative inventory.",
        "citation": "For live use, cite the Hugging Face dataset URL, access date, and manifest hash. Cite the annual Zenodo snapshot for fixed-version academic/legal references once available.",
        "homepage": "https://huggingface.co/datasets/{repo_id}",
        "license": "other"
      }}
    }}
    """)

    placeholders = {
        "README.md": readme,
        ".gitattributes": gitattributes,
        "dataset_infos.json": dataset_infos,
        "manifests/README.md": "Machine-readable manifests will be written here by the pipeline.\n",
        "parquet/README.md": "Partitioned Parquet files will be written here by the pipeline.\n",
        "raw_xml/README.md": "Raw XML/HTML provenance files will be written here by the pipeline where available.\n",
    }

    # upload_file makes one commit per file. That is acceptable for this tiny bootstrap and avoids
    # needing a temporary checkout or git-lfs install on the caller's machine.
    for path_in_repo, content in placeholders.items():
        api.upload_file(
            repo_id=repo_id,
            repo_type="dataset",
            path_in_repo=path_in_repo,
            path_or_fileobj=content.encode("utf-8"),
            commit_message="Initialize dataset repository metadata",
        )

    # v0.4 briefly used data/... placeholders, but the workflow downloads the dataset repo into
    # a local data/ directory and uploads that directory's contents at repository root. Remove
    # any old data-prefixed placeholders so they do not get re-ingested as corpus content.
    for legacy_path in ["data/README.md", "data/manifests/README.md", "data/parquet/README.md"]:
        with suppress(Exception):
            api.delete_file(
                repo_id=repo_id,
                repo_type="dataset",
                path_in_repo=legacy_path,
                commit_message="Remove legacy data-prefixed bootstrap placeholder",
            )

    print(f"Hugging Face dataset repo ready: https://huggingface.co/datasets/{repo_id}")
    print(f"API returned: {repo_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
