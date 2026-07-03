from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate
from typer.testing import CliRunner

from nz_legislation_corpus.cli import app
from nz_legislation_corpus.nzlii_gazette_archive import (
    NZLII_GAZETTE_ROBOTS_URL,
    NZLII_GAZETTE_SOURCE_URLS,
    build_nzlii_gazette_archive,
    build_nzlii_gazette_manifest,
    build_nzlii_gazette_review,
    export_nzlii_gazette_source,
    probe_nzlii_gazette_access,
)


class _FakeResponse:
    def __init__(self, *, url: str, status_code: int, text: str) -> None:
        self.url = url
        self.status_code = status_code
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._text.encode("utf-8")


class _FakeSession:
    def __init__(self, responses: dict[str, _FakeResponse]) -> None:
        self._responses = responses
        self.closed = False

    def get(self, url: str, headers: dict[str, str] | None = None) -> _FakeResponse:  # noqa: ARG002
        return self._responses[url]

    def close(self) -> None:
        self.closed = True


def _blocked_responses() -> dict[str, _FakeResponse]:
    robots_text = (
        "User-agent: *\n"
        "Disallow:\n"
        "Content-Signal: search=yes,ai-train=no,use=reference\n"
    )
    challenge_text = "<html><body>Just a moment...</body></html>"
    return {
        NZLII_GAZETTE_ROBOTS_URL: _FakeResponse(
            url=NZLII_GAZETTE_ROBOTS_URL,
            status_code=200,
            text=robots_text,
        ),
        NZLII_GAZETTE_SOURCE_URLS[0]: _FakeResponse(
            url=NZLII_GAZETTE_SOURCE_URLS[0],
            status_code=403,
            text=challenge_text,
        ),
        NZLII_GAZETTE_SOURCE_URLS[1]: _FakeResponse(
            url=NZLII_GAZETTE_SOURCE_URLS[1],
            status_code=403,
            text=challenge_text,
        ),
    }


def test_probe_nzlii_gazette_access_records_blocked_state() -> None:
    probe = probe_nzlii_gazette_access(session=_FakeSession(_blocked_responses()))

    assert probe["access_status"] == "blocked"
    assert probe["blocked_reason"] == "cloudflare_or_managed_content_challenge"
    assert probe["robots_accessible"] is True
    assert probe["robots_content_signal"] == {
        "search": "yes",
        "ai-train": "no",
        "use": "reference",
    }


def test_export_nzlii_gazette_source_writes_reviewable_blocked_evidence(tmp_path: Path) -> None:
    output_dir = tmp_path / "data" / "nzlii-gazette"
    result = export_nzlii_gazette_source(
        output_dir=output_dir,
        candidate_urls=list(NZLII_GAZETTE_SOURCE_URLS),
        session=_FakeSession(_blocked_responses()),
    )

    schema = json.loads(
        (Path.cwd() / "schemas" / "nz_gazette_raw_source_record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    records = [
        json.loads(line)
        for line in (output_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert result["ok"]
    assert result["review"]["ok"]
    assert result["record_count"] == 1
    assert records[0]["source_id"] == "nzlii_gazette"
    assert records[0]["coverage_state"] == "blocked"
    validate(records[0], schema)
    assert (output_dir / "source_records.jsonl").exists()
    assert (output_dir / "manifests" / "latest_manifest.json").exists()
    assert (output_dir / "manifests" / "validation_report.json").exists()
    assert (output_dir / "manifests" / "coverage_report.json").exists()
    assert (output_dir / "_state" / "source_state.json").exists()

    manifest = build_nzlii_gazette_manifest(
        source_records=records,
        probe_result=result["probe_result"],
    )
    manifest_schema = json.loads(
        (Path.cwd() / "schemas" / "nzlii_gazette_archive_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    review = build_nzlii_gazette_review(
        source_records=records,
        manifest=manifest,
        probe_result=result["probe_result"],
        source_records_path=output_dir / "source_records.jsonl",
        records_path=output_dir / "records.jsonl",
        raw_probe_path=output_dir / "raw" / "probe" / "source_state.json",
        state_path=output_dir / "_state" / "source_state.json",
    )

    assert manifest["record_count"] == 1
    assert manifest["record_kind_counts"] == {"blocked_evidence": 1}
    validate(manifest, manifest_schema)
    assert review["ok"]
    assert review["blocked_count"] == 1


def test_nzlii_gazette_archive_cli_bundles_source_state(tmp_path: Path) -> None:
    source_dir = tmp_path / "data" / "nzlii-gazette"
    output_dir = tmp_path / "dist" / "nzlii-gazette"
    export_nzlii_gazette_source(
        output_dir=source_dir,
        candidate_urls=list(NZLII_GAZETTE_SOURCE_URLS),
        session=_FakeSession(_blocked_responses()),
    )

    archive = build_nzlii_gazette_archive(source_dir, output_dir, year="2026")
    assert Path(archive["archive_path"]).exists()
    assert Path(archive["manifest_path"]).exists()
    assert Path(archive["provenance_path"]).exists()
    assert Path(archive["checksums_path"]).exists()

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "nzlii-gazette-archive",
            "--source-dir",
            str(source_dir),
            "--output-dir",
            str(output_dir),
            "--year",
            "2026",
        ],
    )

    assert result.exit_code == 0, result.output
    assert any(
        path.name.endswith(".tar.zst") or path.name.endswith(".tar.gz")
        for path in output_dir.iterdir()
    )
