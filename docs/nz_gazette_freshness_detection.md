# NZ Gazette Freshness Detection

Track 48 adds a bounded freshness layer for the New Zealand Gazette archive
family. It detects new or changed material from the official Gazette feed and
from a bounded DigitalNZ Gazette poll, then emits targeted refresh queues for
the source-specific archive tracks and the derived canonical track.

## Purpose

Freshness detection is advisory. It finds change signals and route decisions;
it does not replace the immutable raw source archives or the canonical
comparison layer.

## Inputs

- Official Gazette RSS/Atom feed downloaded from the current Gazette site or
  API-supported feed endpoint.
- Bounded DigitalNZ Gazette poll using the local `dnz` exporter or the
  documented DigitalNZ API query path.
- Optional previous freshness state for idempotent reruns.

## Outputs

The freshness command writes:

- `freshness_state.jsonl`
- `refresh_queue.jsonl`
- `review_candidates.jsonl`
- `freshness_report.json`
- `source_index.json`
- source-specific official and DigitalNZ artifact trees under the output
  directory

## Queue Targets

- Track 42 for official Gazette refreshes
- Track 43 for DigitalNZ Gazette refreshes
- Track 44 for historical Gazette refreshes
- Track 45 for NZLII redundancy refreshes
- Track 46 for canonical rebuilds affected by the source changes

## State Model

Freshness state records preserve:

- source ID
- item ID
- source URL
- title
- content hash
- first-seen and last-seen timestamps
- status
- blocked or review reason
- targeted track IDs
- source-artifact path

Statuses are recorded explicitly as:

- `new`
- `changed`
- `unchanged`
- `duplicate`
- `withdrawn`
- `deleted`
- `blocked`

## Workflow

The workflow `.github/workflows/nz_gazette_freshness_detection.yml` downloads
the official feed, runs `nzlc gazette-freshness-detect`, and uploads the
resulting artifact bundle for review.

## Notes

The freshness layer consumes the same source contract as Tracks 42-47. It keeps
source-specific evidence separate and only emits canonical rebuild queues for
affected records or bounded windows.
