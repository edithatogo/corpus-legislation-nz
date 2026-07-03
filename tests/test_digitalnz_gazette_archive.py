from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from nz_legislation_corpus.digitalnz_gazette import (
    build_digitalnz_gazette_archive,
    build_digitalnz_gazette_manifest,
    build_digitalnz_gazette_query_plan,
    build_digitalnz_gazette_review,
    export_digitalnz_gazette_source,
    normalize_digitalnz_gazette_item,
)


def _digitalnz_item(*, item_id: str, title: str, has_rights: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": item_id,
        "title": title,
        "description": f"Description for {title}",
        "display_url": f"https://digitalnz.org/records/{item_id}",
        "source_url": f"https://example.org/{item_id}.pdf",
        "collection": ["New Zealand Gazette"],
        "content_partner": ["DigitalNZ"],
        "creator": ["Office of the Clerk"],
        "category": ["Text"],
        "date": ["2026-07-03"],
        "syndication_date": "2026-07-03T00:00:00Z",
    }
    if has_rights:
        payload["rights_statement"] = "DigitalNZ record rights statement."
        payload["rights_url"] = "https://example.org/rights"
    return payload


def test_build_digitalnz_gazette_query_plan_is_deterministic() -> None:
    plan = build_digitalnz_gazette_query_plan(
        query_text="Gazette",
        collection_filter="New Zealand Gazette",
        page_size=25,
        start_page=2,
        max_pages=3,
        dnz_repo_root=Path("C:/Users/60217257/OneDrive - Flinders/repos/legal-nz/dnz"),
    )
    same_plan = build_digitalnz_gazette_query_plan(
        query_text="Gazette",
        collection_filter="New Zealand Gazette",
        page_size=25,
        start_page=2,
        max_pages=3,
        dnz_repo_root=Path("C:/Users/60217257/OneDrive - Flinders/repos/legal-nz/dnz"),
    )

    assert plan["query_text"] == "Gazette"
    assert plan["collection_filter"] == "New Zealand Gazette"
    assert plan["page_size"] == 25
    assert plan["start_page"] == 2
    assert plan["max_pages"] == 3
    assert plan["api_access_mode"] == "key_required"
    assert plan["query_sha256"] == same_plan["query_sha256"]


def test_normalize_digitalnz_gazette_item_preserves_rights_and_urls(tmp_path: Path) -> None:
    plan = build_digitalnz_gazette_query_plan(
        query_text="Gazette",
        collection_filter="New Zealand Gazette",
        page_size=25,
    )
    page_meta = {
        "requested_page": 1,
        "api_url": "https://api.digitalnz.org/v3/records.json",
        "query_sha256": plan["query_sha256"],
        "request_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "retrieved_at_utc": "2026-07-03T00:00:00+00:00",
    }
    raw_page_path = tmp_path / "raw" / "pages" / "page-0001.json"
    raw_page_path.parent.mkdir(parents=True, exist_ok=True)
    raw_page_path.write_text("{}", encoding="utf-8")
    raw_item_path = tmp_path / "raw" / "items" / "item-1.json"
    raw_item_path.parent.mkdir(parents=True, exist_ok=True)
    raw_item_path.write_text("{}", encoding="utf-8")
    item = _digitalnz_item(item_id="item-1", title="Notice 1")

    raw_record, normalized = normalize_digitalnz_gazette_item(
        item=item,
        plan=plan,
        page_meta=page_meta,
        page_number=1,
        page_position=1,
        raw_page_path=raw_page_path,
        raw_item_path=raw_item_path,
    )

    schema = json.loads(
        (Path.cwd() / "schemas" / "nz_gazette_raw_source_record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validate(raw_record, schema)

    assert normalized["landing_url"] == "https://digitalnz.org/records/item-1"
    assert normalized["source_url"] == "https://example.org/item-1.pdf"
    assert normalized["rights_note"] == "DigitalNZ record rights statement."
    assert normalized["coverage_state"] == "complete"
    assert raw_record["source_url"] == "https://example.org/item-1.pdf"
    assert raw_record["extraction"]["rights_metadata"]["rights_url"] == "https://example.org/rights"
    assert raw_record["provenance"]["query_sha256"] == plan["query_sha256"]


def test_digitalnz_review_flags_missing_rights(tmp_path: Path) -> None:
    plan = build_digitalnz_gazette_query_plan()
    page_meta = {
        "requested_page": 1,
        "api_url": "https://api.digitalnz.org/v3/records.json",
        "query_sha256": plan["query_sha256"],
        "request_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "retrieved_at_utc": "2026-07-03T00:00:00+00:00",
    }
    raw_page_path = tmp_path / "raw" / "pages" / "page-0001.json"
    raw_page_path.parent.mkdir(parents=True, exist_ok=True)
    raw_page_path.write_text("{}", encoding="utf-8")
    raw_item_path = tmp_path / "raw" / "items" / "item-2.json"
    raw_item_path.parent.mkdir(parents=True, exist_ok=True)
    raw_item_path.write_text("{}", encoding="utf-8")
    raw_record, normalized = normalize_digitalnz_gazette_item(
        item=_digitalnz_item(item_id="item-2", title="Notice 2", has_rights=False),
        plan=plan,
        page_meta=page_meta,
        page_number=1,
        page_position=1,
        raw_page_path=raw_page_path,
        raw_item_path=raw_item_path,
    )
    manifest = build_digitalnz_gazette_manifest(
        source_records=[raw_record],
        normalized_records=[normalized],
        plan=plan,
        page_summaries=[
            {
                "page_number": 1,
                "raw_page_path": str(raw_page_path),
                "raw_page_sha256": "c" * 64,
                "page_request_sha256": page_meta["request_sha256"],
                "page_response_sha256": page_meta["response_sha256"],
                "result_count": 1,
                "retrieved_at_utc": page_meta["retrieved_at_utc"],
                "api_url": page_meta["api_url"],
            }
        ],
        source_records_path=Path("source_records.jsonl"),
        records_path=Path("records.jsonl"),
        raw_pages_dir=Path("raw/pages"),
        state_path=Path("_state/export_state.json"),
    )
    review = build_digitalnz_gazette_review(
        source_records=[raw_record],
        normalized_records=[normalized],
        manifest=manifest,
        page_summaries=manifest["pages"],
        source_records_path=tmp_path / "source_records.jsonl",
        records_path=tmp_path / "records.jsonl",
        raw_pages_dir=tmp_path / "raw" / "pages",
        state_path=tmp_path / "_state" / "export_state.json",
    )

    assert not review["ok"]
    assert review["missing_rights_count"] == 1


def test_digitalnz_review_flags_missing_original_source_url(tmp_path: Path) -> None:
    plan = build_digitalnz_gazette_query_plan()
    page_meta = {
        "requested_page": 1,
        "api_url": "https://api.digitalnz.org/v3/records.json",
        "query_sha256": plan["query_sha256"],
        "request_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "retrieved_at_utc": "2026-07-03T00:00:00+00:00",
    }
    raw_page_path = tmp_path / "raw" / "pages" / "page-0001.json"
    raw_page_path.parent.mkdir(parents=True, exist_ok=True)
    raw_page_path.write_text("{}", encoding="utf-8")
    raw_item_path = tmp_path / "raw" / "items" / "item-3.json"
    raw_item_path.parent.mkdir(parents=True, exist_ok=True)
    raw_item_path.write_text("{}", encoding="utf-8")
    item = _digitalnz_item(item_id="item-3", title="Notice 3")
    item.pop("source_url")

    raw_record, normalized = normalize_digitalnz_gazette_item(
        item=item,
        plan=plan,
        page_meta=page_meta,
        page_number=1,
        page_position=1,
        raw_page_path=raw_page_path,
        raw_item_path=raw_item_path,
    )
    review = build_digitalnz_gazette_review(
        source_records=[raw_record],
        normalized_records=[normalized],
        manifest={
            "manifest_sha256": "c" * 64,
            "content_sha256": "d" * 64,
            "page_count": 1,
            "raw_record_count": 1,
            "normalized_record_count": 1,
        },
        page_summaries=[
            {
                "page_number": 1,
                "raw_page_path": str(raw_page_path),
                "raw_page_sha256": "c" * 64,
                "page_request_sha256": page_meta["request_sha256"],
                "page_response_sha256": page_meta["response_sha256"],
                "result_count": 1,
                "retrieved_at_utc": page_meta["retrieved_at_utc"],
                "api_url": page_meta["api_url"],
            }
        ],
        source_records_path=raw_page_path.parent.parent / "source_records.jsonl",
        records_path=raw_page_path.parent.parent / "records.jsonl",
        raw_pages_dir=raw_page_path.parent,
        state_path=raw_page_path.parent.parent / "_state" / "export_state.json",
    )

    assert not review["ok"]
    assert review["missing_original_source_url_count"] == 1


def test_export_and_archive_build_smoke(tmp_path: Path, monkeypatch) -> None:
    responses = {
        1: {
            "search": {
                "result_count": 2,
                "results": [_digitalnz_item(item_id="item-1", title="Notice 1")],
            }
        },
        2: {
            "search": {
                "result_count": 2,
                "results": [_digitalnz_item(item_id="item-2", title="Notice 2")],
            }
        },
        3: {"search": {"result_count": 2, "results": []}},
    }

    def fake_fetch(*, plan, page, api_key, session=None):
        payload = responses[page]
        meta = {
            "requested_page": page,
            "api_url": plan["api_url"],
            "query_sha256": plan["query_sha256"],
            "result_count": payload["search"]["result_count"],
            "returned_count": len(payload["search"]["results"]),
            "retrieved_at_utc": f"2026-07-03T00:00:0{page}+00:00",
            "request_sha256": f"{page}" * 64,
            "response_sha256": f"{page + 1}" * 64,
        }
        return payload, meta

    monkeypatch.setattr(
        "nz_legislation_corpus.digitalnz_gazette._fetch_digitalnz_page",
        fake_fetch,
    )

    export_dir = tmp_path / "data" / "digitalnz-gazette"
    result = export_digitalnz_gazette_source(
        output_dir=export_dir,
        api_key="test-key",
        max_pages=2,
    )

    manifest_schema = json.loads(
        (Path.cwd() / "schemas" / "digitalnz_gazette_export_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads((export_dir / "manifests" / "latest_manifest.json").read_text(encoding="utf-8"))
    validate(manifest, manifest_schema)

    assert result["ok"]
    assert (export_dir / "source_records.jsonl").exists()
    assert (export_dir / "records.jsonl").exists()
    assert (export_dir / "manifests" / "validation_report.json").exists()
    assert (export_dir / "manifests" / "coverage_report.json").exists()
    assert (export_dir / "_state" / "export_state.json").exists()

    archive_dir = tmp_path / "dist" / "digitalnz-gazette"
    archive = build_digitalnz_gazette_archive(export_dir, archive_dir, year="2026")
    assert Path(archive["archive_path"]).exists()
    assert Path(archive["archive_manifest_path"]).exists()
    assert Path(archive["release_evidence_path"]).exists()
