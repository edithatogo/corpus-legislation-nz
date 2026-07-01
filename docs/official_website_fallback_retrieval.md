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
exposes these pieces:

1. `OfficialWebsiteFallbackPolicy` for the allowed-host and browser policy.
2. `build_failed_record_retry_plan(...)` for a single failed record.
3. `plan_failed_record_retries(...)` for a small failed-record batch.
4. `build_playwright_diagnostics_plan(...)` for an explicit, bounded browser
   diagnostics plan.

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

CLI entry points:

- `nzlc plan-website-fallbacks` loads a failed-record JSONL file and writes a
  retry plan without fetching pages.
- `nzlc website-fallback-diagnostics` writes a Playwright diagnostics plan and
  script from a retry plan. It does not launch a browser unless `--run` is
  passed, and rendered captures remain low-confidence manual triage artifacts.
