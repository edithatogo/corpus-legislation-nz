from pathlib import Path

import pytest

from nz_legislation_corpus.manifest import build_manifest


@pytest.mark.unit
def test_build_manifest(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    manifest = build_manifest(tmp_path)
    assert manifest["files"][0]["path"] == "a.txt"
    assert manifest["manifest_sha256"]


@pytest.mark.unit
def test_manifest_content_hash_stable_for_unchanged_content(tmp_path):
    from nz_legislation_corpus.manifest import build_manifest

    root = tmp_path / "data"
    root.mkdir()
    (root / "records.jsonl").write_text('{"stable_id":"a"}\n', encoding="utf-8")
    first = build_manifest(root)
    second = build_manifest(root)
    assert first["content_sha256"] == second["content_sha256"]


@pytest.mark.unit
def test_manifest_excludes_state_and_cache(tmp_path):
    from nz_legislation_corpus.manifest import build_manifest

    root = tmp_path / "data"
    (root / "_state").mkdir(parents=True)
    (root / "cache" / "huggingface").mkdir(parents=True)
    (root / ".cache" / "huggingface" / "download").mkdir(parents=True)
    (root / "records.jsonl").write_text('{"stable_id":"a"}\n', encoding="utf-8")
    (root / "_state" / "sync_state.json").write_text('{"run":1}', encoding="utf-8")
    (root / "cache" / "huggingface" / "tmp").write_text("cache", encoding="utf-8")
    (root / ".cache" / "huggingface" / "download" / "tmp.metadata").write_text(
        "cache", encoding="utf-8"
    )
    manifest = build_manifest(root)
    paths = {f["path"] for f in manifest["files"]}
    assert "records.jsonl" in paths
    assert not any(path.startswith("_state/") for path in paths)
    assert not any(path.startswith("cache/") for path in paths)
    assert not any(path.startswith(".cache/") for path in paths)
    assert not any(path.startswith("_state/") for path in paths)
    assert not any(path.startswith("cache/") for path in paths)
    assert not any(path.startswith(".cache/") for path in paths)


@pytest.mark.unit
def test_build_manifest_empty_directory(tmp_path: Path) -> None:
    from nz_legislation_corpus.manifest import build_manifest

    manifest = build_manifest(tmp_path)
    assert manifest["files"] == []
    assert manifest["record_count"] is None
    assert manifest["manifest_sha256"] is not None
    assert manifest["content_sha256"] is not None


@pytest.mark.unit
def test_build_manifest_nested_subdirectories(tmp_path: Path) -> None:
    from nz_legislation_corpus.manifest import build_manifest

    (tmp_path / "raw_xml").mkdir()
    (tmp_path / "raw_xml" / "a.xml").write_text("<a/>", encoding="utf-8")
    (tmp_path / "parquet" / "year=2026").mkdir(parents=True)
    (tmp_path / "parquet" / "year=2026" / "file.parquet").write_bytes(b"data")
    (tmp_path / "manifests").mkdir()
    (tmp_path / "manifests" / "latest_manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "records.jsonl").write_text("{}\n", encoding="utf-8")

    manifest = build_manifest(tmp_path)
    paths = [f["path"] for f in manifest["files"]]

    assert "raw_xml/a.xml" in paths
    assert "parquet/year=2026/file.parquet" in paths
    assert "records.jsonl" in paths
    # manifests/ is excluded
    assert not any(p.startswith("manifests/") for p in paths)
    for entry in manifest["files"]:
        assert "sha256" in entry
        assert "size_bytes" in entry
        assert "modified_time_utc" in entry


@pytest.mark.unit
def test_build_change_report_no_previous() -> None:
    from nz_legislation_corpus.manifest import build_change_report

    current = {
        "manifest_sha256": "abc",
        "content_sha256": "def",
        "files": [{"path": "a.txt", "sha256": "h1"}],
    }
    report = build_change_report(None, current)

    assert report["added"] == ["a.txt"]
    assert report["removed"] == []
    assert report["changed"] == []
    assert report["has_changes"] is True
    assert report["previous_manifest_sha256"] is None
    assert report["current_manifest_sha256"] == "abc"


@pytest.mark.unit
def test_build_change_report_no_changes() -> None:
    from nz_legislation_corpus.manifest import build_change_report

    previous = {
        "manifest_sha256": "abc",
        "content_sha256": "def",
        "files": [{"path": "a.txt", "sha256": "h1"}],
    }
    current = {
        "manifest_sha256": "abc",
        "content_sha256": "def",
        "files": [{"path": "a.txt", "sha256": "h1"}],
    }
    report = build_change_report(previous, current)

    assert report["added"] == []
    assert report["removed"] == []
    assert report["changed"] == []
    assert report["has_changes"] is False


@pytest.mark.unit
def test_build_change_report_added_removed_changed() -> None:
    from nz_legislation_corpus.manifest import build_change_report

    previous = {
        "manifest_sha256": "abc",
        "content_sha256": "def",
        "files": [
            {"path": "a.txt", "sha256": "h1"},
            {"path": "b.txt", "sha256": "h2"},
        ],
    }
    current = {
        "manifest_sha256": "xyz",
        "content_sha256": "uvw",
        "files": [
            {"path": "a.txt", "sha256": "h1_changed"},
            {"path": "c.txt", "sha256": "h3"},
        ],
    }
    report = build_change_report(previous, current)

    assert report["added"] == ["c.txt"]
    assert report["removed"] == ["b.txt"]
    assert report["changed"] == ["a.txt"]
    assert report["has_changes"] is True
