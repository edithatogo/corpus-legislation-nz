# Official Website Fallback Retrieval

This track adds a conservative recovery path for records that already failed the
API XML, advertised HTML, or alternate dated URL attempts.

The fallback is deliberately narrow:

- It only accepts public `https://` URLs on the official NZ Legislation host.
- It fails closed when no eligible public official URL is available.
- It does not implement stealth mode, CAPTCHA bypass, credentialed scraping, or
  broad crawling.
- Browser rendering is treated as an optional diagnostic hook, not a canonical
  ingestion path.

The current tooling lives in `src/nz_legislation_corpus/website_fallback.py` and
exposes three pieces:

1. `OfficialWebsiteFallbackPolicy` for the allowed-host and browser policy.
2. `build_failed_record_retry_plan(...)` for a single failed record.
3. `plan_failed_record_retries(...)` for a small failed-record batch.

Each fallback attempt keeps provenance fields that can be surfaced in sync
state, review output, or manual triage:

- `source_url`
- `retrieval_method`
- `retrieval_timestamp_utc`
- `content_hash`
- `previous_failure_reason`
- `confidence`
- `status`

The retry planner is intentionally conservative. It only produces plans for
eligible public official URLs, and it stops once the small configured record
limit is reached.

Planned integration hooks, not yet wired here:

- A CLI command for loading a failed-record list and emitting a retry plan.
- Review-report plumbing that counts browser fallback records separately from
  XML-to-HTML fallback warnings.
- Optional Playwright-based execution for triage runs, isolated from the normal
  API-first sync path.
