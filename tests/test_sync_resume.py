from __future__ import annotations

import json
from pathlib import Path

from nz_legislation_corpus import cli


class FakeNZLegislationClient:
    calls = 0

    def __init__(self, settings):
        self.settings = settings

    def discover_versions(self, **kwargs):
        FakeNZLegislationClient.calls += 1
        limit = kwargs.get("max_works")
        records = [
            {
                "title": "Resume Test Act 2026",
                "version_id": "resume-test-act-2026/latest",
                "work_id": "resume-test-act-2026",
                "legislation_status": "current",
                "legislation_type": "act",
                "administering_agencies": ["Example Agency"],
                "formats": [],
                "is_latest_version": True,
            },
            {
                "title": "Resume Test Regulation 2026",
                "version_id": "resume-test-regulation-2026/latest",
                "work_id": "resume-test-regulation-2026",
                "legislation_status": "current",
                "legislation_type": "secondary_legislation",
                "administering_agencies": ["Example Agency"],
                "formats": [],
                "is_latest_version": True,
            },
        ]
        yield from records[:limit]

    @staticmethod
    def format_url(version, fmt):
        return None


def test_sync_preserves_state_between_batches(tmp_path: Path, monkeypatch):
    output_dir = tmp_path / "data"
    seed_path = tmp_path / "seed.txt"
    seed_path.write_text("resume-test-act-2026\nresume-test-regulation-2026\n", encoding="utf-8")
    monkeypatch.setenv("NZ_LEGISLATION_API_KEY", "test-key")
    monkeypatch.setenv("NZLC_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("NZLC_SEARCH_TERMS", "")
    monkeypatch.setattr(cli, "NZLegislationClient", FakeNZLegislationClient)
    monkeypatch.setattr(cli, "write_partitioned_parquet", lambda records, output_dir: [])
    FakeNZLegislationClient.calls = 0

    cli.sync(
        seed_work_ids=seed_path,
        latest_only=False,
        max_works=1,
        allow_no_search_terms=True,
        replace=False,
        embeddings=False,
    )
    first_state = json.loads(
        (output_dir / "_state" / "sync_state.json").read_text(encoding="utf-8")
    )

    cli.sync(
        seed_work_ids=seed_path,
        latest_only=False,
        max_works=2,
        allow_no_search_terms=True,
        replace=False,
        embeddings=False,
    )
    second_state = json.loads(
        (output_dir / "_state" / "sync_state.json").read_text(encoding="utf-8")
    )

    assert FakeNZLegislationClient.calls == 2
    assert set(first_state["versions"]) == {"resume-test-act-2026/latest"}
    assert set(second_state["versions"]) == {
        "resume-test-act-2026/latest",
        "resume-test-regulation-2026/latest",
    }
    assert second_state["last_stats"]["records_unchanged"] == 1
    assert second_state["last_stats"]["records_added"] == 1
