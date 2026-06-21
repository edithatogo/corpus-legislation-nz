from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def guard_target(args: argparse.Namespace) -> None:
    historical_repo_id = (args.historical_repo_id or "").strip()
    live_repo_id = (args.live_repo_id or "").strip()
    forbidden_alias = (args.forbidden_alias or "").strip()

    if not historical_repo_id:
        _fail("HF_HISTORICAL_REPO_ID must be configured as a repository variable.")
    if live_repo_id and historical_repo_id == live_repo_id:
        _fail("HF_HISTORICAL_REPO_ID must not equal HF_REPO_ID.")
    if forbidden_alias and historical_repo_id == forbidden_alias:
        _fail(
            f"Refusing to use the live partial dataset as the historical target: {forbidden_alias}"
        )

    if args.summary_path:
        summary_path = Path(args.summary_path)
        current = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
        summary_path.write_text(
            current + f"Historical dataset target: {historical_repo_id}\n",
            encoding="utf-8",
        )


def seed_provenance(args: argparse.Namespace) -> None:
    seed_path = Path(args.seed_path)
    if not seed_path.is_file():
        _fail(f"Reviewed seed file does not exist: {seed_path.as_posix()}")

    work_ids = [
        line.strip()
        for line in seed_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    unique = sorted(set(work_ids))
    payload = "".join(f"{work_id}\n" for work_id in unique).encode("utf-8")
    provenance = {
        "schema_version": "1.0",
        "source": "reviewed_seed_file",
        "seed_work_ids_path": seed_path.as_posix(),
        "source_record_count": len(work_ids),
        "unique_record_count": len(unique),
        "seed_sha256": hashlib.sha256(payload).hexdigest(),
        "coverage_warning": (
            "This seed is only as complete as the reviewed source inventory. "
            "Do not claim full historical coverage until reconciliation is complete."
        ),
    }
    Path(args.output_path).write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )


def publication_policy(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    manifests_dir = output_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    policy = {
        "schema_version": "1.0",
        "policy": "manual_historical_upload",
        "historical_huggingface_dataset": args.historical_repo_id,
        "live_huggingface_dataset": args.live_repo_id,
        "live_dataset_boundary": "verified partial/API-discovery corpus",
        "seed_work_ids_path": args.seed_work_ids_path,
        "merge_policy": args.merge_policy,
        "guards": [
            "HF_HISTORICAL_REPO_ID is required.",
            "HF_HISTORICAL_REPO_ID must not equal HF_REPO_ID.",
            "The live partial dataset is explicitly refused as a historical target.",
            "The workflow has no schedule and defaults to no-upload dry run.",
            "Confirmed incremental uploads require merge_policy=restore_merge unless merge_policy=replace_existing.",
        ],
    }
    manifests_dir.joinpath("publication_policy.json").write_text(
        json.dumps(policy, indent=2) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared helper for historical workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    guard = subparsers.add_parser("guard-target")
    guard.add_argument("--historical-repo-id", default="")
    guard.add_argument("--live-repo-id", default="")
    guard.add_argument("--forbidden-alias", default="edithatogo/nz-legislation-corpus")
    guard.add_argument("--summary-path", default="")
    guard.set_defaults(func=guard_target)

    seed = subparsers.add_parser("seed-provenance")
    seed.add_argument("--seed-path", required=True)
    seed.add_argument("--output-path", required=True)
    seed.set_defaults(func=seed_provenance)

    policy = subparsers.add_parser("publication-policy")
    policy.add_argument("--historical-repo-id", required=True)
    policy.add_argument("--live-repo-id", default="")
    policy.add_argument("--seed-work-ids-path", required=True)
    policy.add_argument("--merge-policy", required=True)
    policy.add_argument("--output-dir", required=True)
    policy.set_defaults(func=publication_policy)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
