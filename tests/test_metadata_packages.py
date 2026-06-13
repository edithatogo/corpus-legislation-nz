from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nz_legislation_corpus.cli import app
from nz_legislation_corpus.metadata_packages import PACKAGE_FILENAMES, build_metadata_packages


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
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
    prov = json.loads((output_dir / "prov-o.jsonld").read_text())
    generated = prov["@graph"][2]["prov:generated"]
    assert {"@id": "croissant.json"} in generated


@pytest.mark.unit
def test_validate_metadata_packages_missing_dir(tmp_path: Path) -> None:
    from nz_legislation_corpus.metadata_packages import validate_metadata_packages

    missing_dir = tmp_path / "nonexistent"
    result = validate_metadata_packages(missing_dir, root=Path.cwd())
    assert result["ok"] is False
    assert any("is missing" in err for err in result["errors"])


@pytest.mark.unit
def test_validate_metadata_packages_invalid_json(tmp_path: Path) -> None:
    from nz_legislation_corpus.metadata_packages import validate_metadata_packages

    for filename in PACKAGE_FILENAMES.values():
        (tmp_path / filename).write_text("not valid json", encoding="utf-8")

    result = validate_metadata_packages(tmp_path, root=Path.cwd())
    assert result["ok"] is False
    assert any("not valid JSON" in err for err in result["errors"])


@pytest.mark.unit
def test_validate_metadata_packages_missing_keys(tmp_path: Path) -> None:
    from nz_legislation_corpus.metadata_packages import validate_metadata_packages

    # Write package files with minimal content (missing required keys)
    package_content = {
        "croissant.json": json.dumps({"name": "no-type"}),
        "ro-crate-metadata.json": json.dumps({"@context": "https://w3id.org/ro/crate/1.1/context"}),
        "datapackage.json": json.dumps({"name": "no-profile"}),
        "dcat.jsonld": json.dumps({"@context": {}, "dct:title": "no-distribution"}),
        "prov-o.jsonld": json.dumps({"@context": {}}),
    }
    for filename, content in package_content.items():
        (tmp_path / filename).write_text(content, encoding="utf-8")

    result = validate_metadata_packages(tmp_path, root=Path.cwd())
    assert result["ok"] is False
    # Each package should report missing-key errors
    croissant_errors = result["packages"].get("croissant", {}).get("errors", [])
    assert any("missing" in err for err in croissant_errors)


@pytest.mark.unit
def test_validate_metadata_packages_after_build(tmp_path: Path) -> None:
    from nz_legislation_corpus.metadata_packages import validate_metadata_packages

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

    build_metadata_packages(root, tmp_path / "metadata")
    result = validate_metadata_packages(tmp_path / "metadata", root=root)
    assert result["ok"] is True
    for _pkg_name, pkg_result in result["packages"].items():
        assert pkg_result["exists"] is True
        assert pkg_result["errors"] == []
