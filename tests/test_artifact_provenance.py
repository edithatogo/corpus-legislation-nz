from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from nz_legislation_corpus.archive import build_archive

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_artifact_provenance import failures  # noqa: E402


def _write_fixture_corpus(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "records.jsonl").write_text(
        json.dumps(
            {
                "stable_id": "example-1",
                "record_schema_version": "1.0",
                "text": "Example legislation text",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "raw_xml").mkdir()
    (root / "raw_xml" / "example.xml").write_text("<root />\n", encoding="utf-8")


def test_archive_writes_release_evidence_and_checksums(tmp_path: Path) -> None:
    input_dir = tmp_path / "data"
    output_dir = tmp_path / "archive"
    _write_fixture_corpus(input_dir)

    result = build_archive(input_dir, output_dir, year="2026", prefer_zstd=False)

    provenance_path = Path(result["provenance_path"])
    assert provenance_path.exists()
    evidence = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert evidence["artifact_class"] == "annual_zenodo_archive"
    assert evidence["corpus_family_label"] == "corpus-nz-legislation"
    assert evidence["sibling_corpus"] == "corpus-nz-hansard"
    assert evidence["manifest"]["record_count"] == 1
    assert {subject["path"] for subject in evidence["subjects"]} == {
        Path(result["archive_path"]).name,
        Path(result["manifest_path"]).name,
    }

    schema = json.loads((ROOT / "schemas" / "release_evidence.schema.json").read_text())
    Draft202012Validator(schema).validate(evidence)

    checksums = Path(result["checksums_path"]).read_text(encoding="utf-8")
    assert Path(result["archive_path"]).name in checksums
    assert Path(result["manifest_path"]).name in checksums
    assert provenance_path.name in checksums


def test_artifact_provenance_policy_is_consistent() -> None:
    assert failures() == []
