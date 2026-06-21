from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from nz_legislation_corpus.cli import app
from nz_legislation_corpus.metadata_packages import PACKAGE_FILENAMES, build_metadata_packages


def test_build_metadata_packages_writes_expected_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "metadata"
    # Use a clean root with schemas but no data/ manifest to avoid pollution
    root = tmp_path / "root"
    root.mkdir()
    for schema in [
        "schemas/shared_nz_corpus_core.schema.json",
        "schemas/legislation_record.schema.json",
    ]:
        src = Path.cwd() / schema
        dst = root / schema
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text())

    result = build_metadata_packages(root, output_dir)

    assert result["ok"] is True
    for filename in PACKAGE_FILENAMES.values():
        assert (output_dir / filename).exists()
    assert (output_dir / "metadata-package-manifest.json").exists()
    assert (output_dir / "SHA256SUMS.txt").exists()

    manifest = json.loads((output_dir / "metadata-package-manifest.json").read_text())
    assert manifest["source_manifest"]["path"] == "schemas/shared_nz_corpus_core.schema.json"
    assert manifest["publication_surfaces"]["github"].endswith("/corpus-legislation-nz")
    assert manifest["publication_surfaces"]["osf"] is None
    assert manifest["coverage_status"] == "partial"

    checksums = (output_dir / "SHA256SUMS.txt").read_text()
    assert "croissant.json" in checksums
    assert "ro-crate-metadata.json" in checksums
    assert "datapackage.json" in checksums
    assert "dcat.jsonld" in checksums
    assert "prov-o.jsonld" in checksums


def test_metadata_packages_cli_generates_and_validates(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "metadata"

    generate = runner.invoke(app, ["metadata-packages", "--output-dir", str(output_dir)])
    assert generate.exit_code == 0, generate.output

    validate = runner.invoke(
        app,
        ["validate-metadata-packages", "--metadata-dir", str(output_dir)],
    )
    assert validate.exit_code == 0, validate.output


def test_metadata_package_payloads_include_family_labels(tmp_path: Path) -> None:
    output_dir = tmp_path / "metadata"
    build_metadata_packages(Path.cwd(), output_dir)

    frictionless = json.loads((output_dir / "datapackage.json").read_text())
    assert frictionless["custom"]["preferred_family_label"] == "corpus-nz-legislation"
    assert frictionless["custom"]["sibling_corpus"] == "corpus-nz-hansard"

    dcat = json.loads((output_dir / "dcat.jsonld").read_text())
    assert dcat["dct:identifier"] == "corpus-nz-legislation"

    prov = json.loads((output_dir / "prov-o.jsonld").read_text())
    generated = prov["@graph"][2]["prov:generated"]
    assert {"@id": "croissant.json"} in generated
