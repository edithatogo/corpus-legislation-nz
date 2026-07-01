# Feed Change Detection

Track 37 adds an advisory feed-change detector for official NZ Legislation
update signals. The goal is to capture freshness signals without claiming
historical completeness.

## Supported inputs

- RSS 2.0 feeds with `item` entries.
- Atom feeds with `entry` elements.
- Feed payloads loaded from a string, bytes object, or local XML file path.

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
feed-state, refresh-queue, review-candidate, and report artifacts.

## Caveat

This layer is advisory only. It is a freshness signal for the canonical corpus
pipeline, not a substitute for the API-first inventory or full bootstrap.
