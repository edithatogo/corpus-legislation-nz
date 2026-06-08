from pathlib import Path

from nz_legislation_corpus.manifest import build_manifest


def test_build_manifest(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    manifest = build_manifest(tmp_path)
    assert manifest["files"][0]["path"] == "a.txt"
    assert manifest["manifest_sha256"]


def test_manifest_content_hash_stable_for_unchanged_content(tmp_path):
    from nz_legislation_corpus.manifest import build_manifest

    root = tmp_path / "data"
    root.mkdir()
    (root / "records.jsonl").write_text('{"stable_id":"a"}\n', encoding="utf-8")
    first = build_manifest(root)
    second = build_manifest(root)
    assert first["content_sha256"] == second["content_sha256"]


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
