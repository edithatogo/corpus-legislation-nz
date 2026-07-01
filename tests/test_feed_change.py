from __future__ import annotations

import json

import pytest

from nz_legislation_corpus.feed_change import build_feed_change_detection, parse_feed_items


@pytest.mark.unit
def test_build_feed_change_detection_maps_rss_items_and_is_json_serializable() -> None:
    feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>NZ Legislation updates</title>
    <item>
      <title>Newest Bill</title>
      <link>https://www.legislation.govt.nz/bill/government/2025/100/en/latest/</link>
      <guid>bill-government-2025-100-latest</guid>
      <pubDate>Tue, 01 Jul 2026 01:00:00 GMT</pubDate>
      <description>Bill update</description>
    </item>
    <item>
      <title>Exact Act</title>
      <link>https://www.legislation.govt.nz/act/public/2026/26/en/2026-06-01/</link>
      <guid>act-public-2026-26-2026-06-01</guid>
      <updated>2026-06-30T12:30:00Z</updated>
      <description>Act update</description>
    </item>
  </channel>
</rss>
"""

    report = build_feed_change_detection(
        feed_xml,
        feed_url="https://example.invalid/feed.xml",
        retrieved_at="2026-07-01T02:03:04Z",
    )

    json.dumps(report, sort_keys=True)
    assert report["schema_version"] == "1.0"
    assert report["item_count"] == 2
    assert [record["id"] for record in report["state_records"]] == [
        "act-public-2026-26-2026-06-01",
        "bill-government-2025-100-latest",
    ]

    exact = report["state_records"][0]
    assert exact["mapping_status"] == "mapped"
    assert exact["work_id"] == "act_public_2026_26"
    assert exact["version_id"] == "act_public_2026_26_en_2026-06-01"

    latest = report["state_records"][1]
    assert latest["mapping_status"] == "mapped_work_only"
    assert latest["work_id"] == "bill_government_2025_100"
    assert latest["version_id"] is None

    refresh_keys = {
        (record["work_id"], record["version_id"], record["feed_item_id"])
        for record in report["refresh_queue"]
    }
    assert refresh_keys == {
        ("act_public_2026_26", "act_public_2026_26_en_2026-06-01", "act-public-2026-26-2026-06-01"),
        ("bill_government_2025_100", None, "bill-government-2025-100-latest"),
    }


@pytest.mark.unit
def test_build_feed_change_detection_is_idempotent_with_previous_state() -> None:
    feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Exact Act</title>
      <link>https://www.legislation.govt.nz/act/public/2026/26/en/2026-06-01/</link>
      <guid>act-public-2026-26-2026-06-01</guid>
      <pubDate>Tue, 01 Jul 2026 01:00:00 GMT</pubDate>
      <description>Act update</description>
    </item>
  </channel>
</rss>
"""

    first = build_feed_change_detection(feed_xml, retrieved_at="2026-07-01T02:03:04Z")
    second = build_feed_change_detection(
        feed_xml,
        retrieved_at="2026-07-01T02:05:00Z",
        previous_state=first["state_records"],
    )

    assert first["refresh_queue"]
    assert second["refresh_queue"] == []
    assert second["state_records"][0]["content_hash"] == first["state_records"][0]["content_hash"]


@pytest.mark.unit
def test_build_feed_change_detection_reports_unmapped_items_as_review_candidates() -> None:
    feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>NZ Legislation updates</title>
  <entry>
    <title>External notice</title>
    <id>tag:example.invalid,2026:notice-1</id>
    <updated>2026-07-01T02:00:00Z</updated>
    <link rel="alternate" href="https://example.com/not-legislation"/>
    <summary>Needs review</summary>
  </entry>
</feed>
"""

    report = build_feed_change_detection(feed_xml, retrieved_at="2026-07-01T02:03:04Z")

    assert report["item_count"] == 1
    assert report["state_records"][0]["mapping_status"] == "unmapped"
    assert report["refresh_queue"] == []
    assert len(report["review_candidates"]) == 1
    assert report["review_candidates"][0]["feed_item_id"] == "tag:example.invalid,2026:notice-1"


@pytest.mark.unit
def test_build_feed_change_detection_deduplicates_duplicate_feed_entries() -> None:
    feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Exact Act</title>
      <link>https://www.legislation.govt.nz/act/public/2026/26/en/2026-06-01/</link>
      <guid>act-public-2026-26-2026-06-01</guid>
      <pubDate>Tue, 01 Jul 2026 01:00:00 GMT</pubDate>
      <description>Act update</description>
    </item>
    <item>
      <title>Exact Act</title>
      <link>https://www.legislation.govt.nz/act/public/2026/26/en/2026-06-01/</link>
      <guid>act-public-2026-26-2026-06-01</guid>
      <pubDate>Tue, 01 Jul 2026 01:00:00 GMT</pubDate>
      <description>Act update</description>
    </item>
  </channel>
</rss>
"""

    report = build_feed_change_detection(feed_xml, retrieved_at="2026-07-01T02:03:04Z")

    assert report["item_count"] == 1
    assert len(report["state_records"]) == 1
    assert len(report["refresh_queue"]) == 1


@pytest.mark.unit
def test_parse_feed_items_supports_atom_entries() -> None:
    feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>NZ Legislation updates</title>
  <entry>
    <title>Exact Act</title>
    <id>tag:example.invalid,2026:act-1</id>
    <updated>2026-06-30T12:30:00Z</updated>
    <published>2026-06-29T12:30:00Z</published>
    <link rel="alternate" href="https://www.legislation.govt.nz/act/public/2026/26/en/2026-06-01/"/>
    <content type="text">Act update</content>
  </entry>
</feed>
"""

    items = parse_feed_items(feed_xml)

    assert len(items) == 1
    assert items[0]["id"] == "tag:example.invalid,2026:act-1"
    assert items[0]["updated"] == "2026-06-30T12:30:00Z"
    assert items[0]["published"] == "2026-06-29T12:30:00Z"
