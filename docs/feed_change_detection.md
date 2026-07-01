# Feed Change Detection

Track 37 adds an advisory feed-change detector for official NZ Legislation
update signals. The goal is to capture freshness signals without claiming
historical completeness.

## Supported inputs

- RSS 2.0 feeds with `item` entries.
- Atom feeds with `entry` elements.
- Feed payloads loaded from a string, bytes object, or local XML file path.

## Official Source Discovery

The supported official freshness signals are:

- Search-based RSS feeds generated from search result pages on the new NZ
  Legislation website. The website help pages state that saved feeds from the
  earlier website must be regenerated on the new site, and that search results
  expose RSS feeds for keeping up to date.
- The official API RSS search endpoint documented at
  `https://api.legislation.govt.nz/api/rss/search/`.
- The official API `works/` search endpoint for API-driven freshness checks. The
  project maps this to `NZLegislationClient.search_works(...)` with parameters
  `search_term`, `search_field`, `page`, `per_page`, `legislation_type`,
  `legislation_status`, `sort_by`, and `publisher`.

Recommended API freshness settings mirror the existing discovery pipeline:

- `NZLC_SEARCH_SORT_BY=most_recently_updated`
- `NZLC_SEARCH_FIELD=title` or `fulltext`
- broad `NZLC_SEARCH_TERMS` only as a change-detection hint
- optional `NZLC_LEGISLATION_TYPES`, `NZLC_LEGISLATION_STATUS`, and
  `NZLC_PUBLISHER` filters when the queue should be scoped

The API docs describe the API as version zero and search-oriented. This track
therefore treats API/search and RSS results as freshness signals only; they do
not prove full historical coverage.

## Recorded feed item state

Each parsed item is reduced to a JSON-serializable state record with:

- `id`
- `url`
- `title`
- `updated`
- `published`
- `content_hash`
- `retrieved_at`
- `mapping_status`
- `work_id`
- `version_id`

The state hash is computed from the stable item fields so repeated polling stays
auditable.

## URL mapping rules

Legislation URLs under `legislation.govt.nz` are mapped from the path pattern
described in the NZ Legislation API docs:

- `work_id` is derived from the first four path segments.
- `version_id` is derived when the URL contains a concrete version date.
- `latest` URLs are mapped to a `work_id` only, because the exact version is not
  fixed.
- Non-legislation URLs become review candidates.

## Refresh and review outputs

The detector returns two downstream lists:

- `refresh_queue`: mapped items that should be rechecked by the canonical
  API-first downloader.
- `review_candidates`: unmapped items that need coverage review.

The outputs are sorted deterministically and remain JSON-serializable.

## GitHub Actions Entry Point

The workflow `.github/workflows/official_feed_change_detection.yml` accepts an
explicit search-based feed URL through `workflow_dispatch` or the
`NZLC_OFFICIAL_FEED_URL` repository variable. It refuses non-official feed hosts,
downloads the feed, runs `nzlc feed-change-detect`, and uploads the advisory
feed-state, refresh-queue, review-candidate, and report artifacts. If the
`NZ_LEGISLATION_API_KEY` secret is configured, the workflow sends it as an
`X-Api-Key` header so the official API RSS endpoint can be used without placing
the key in the URL.

## Manual Verification Evidence

Track 37 was manually verified on 2026-07-01 with:

- `uv run nzlc feed-change-detect --feed-path generated/track37-manual-verification/feed.xml --output-dir generated/track37-manual-verification/artifacts --feed-url https://www.legislation.govt.nz/search/rss/example --retrieved-at 2026-07-01T00:00:00Z`
- JSON parse checks for `feed_change_report.json`, `feed_state.jsonl`,
  `refresh_queue.jsonl`, and `review_candidates.jsonl`.
- `uv run python -m pytest -q -p no:cacheprovider tests\test_feed_change.py tests\test_official_feed_change_detection_workflow.py tests\smoke\test_cli_smoke.py -q`
- `uv run ruff check --no-cache src\nz_legislation_corpus\feed_change.py src\nz_legislation_corpus\cli.py tests\test_feed_change.py tests\test_official_feed_change_detection_workflow.py`
- `uv run ruff format --check src\nz_legislation_corpus\feed_change.py src\nz_legislation_corpus\cli.py tests\test_feed_change.py tests\test_official_feed_change_detection_workflow.py`
- `uv run ty check src tests`
- `git diff --check`

The Conductor review pass also checked that official-host matching rejects
suffix lookalikes such as `evillegislation.govt.nz`, and that the Actions
workflow explicitly allows `api.legislation.govt.nz` for the documented API RSS
endpoint.

## Caveat

This layer is advisory only. It is a freshness signal for the canonical corpus
pipeline, not a substitute for the API-first inventory or full bootstrap.
