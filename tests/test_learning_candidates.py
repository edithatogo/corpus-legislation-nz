import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "record_learning_candidate.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("record_learning_candidate", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_append_candidate_creates_section_and_is_idempotent(tmp_path: Path) -> None:
    module = _load_module()
    backlog = tmp_path / "improvement-backlog.md"

    inserted, candidate_lines = module.append_candidate(
        backlog,
        "CI failure summary candidate for `Docs`",
        ["workflow=Docs", "run_id=123"],
    )
    inserted_again, duplicate_lines = module.append_candidate(
        backlog,
        "CI failure summary candidate for `Docs`",
        ["workflow=Docs", "run_id=123"],
    )

    assert inserted is True
    assert inserted_again is False
    assert candidate_lines == duplicate_lines
    text = backlog.read_text(encoding="utf-8")
    assert text.count("CI failure summary candidate for `Docs`") == 1
    assert "## Active candidates" in text
    assert "  - workflow=Docs" in text


def test_write_snapshot_creates_parent_directory(tmp_path: Path) -> None:
    module = _load_module()
    snapshot = tmp_path / "conductor" / ".tmp" / "candidate.md"

    module.write_snapshot(str(snapshot), ["- [ ] Candidate", "  - run_id=123"])

    assert snapshot.read_text(encoding="utf-8") == "- [ ] Candidate\n  - run_id=123\n"
