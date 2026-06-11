# Reviewed historical seed batches

This directory contains small reviewed seed batches that are safe to reference
from manual GitHub Actions workflows. They are operational seeds, not proof of
complete historical coverage.

## `historical-work-ids-0001.txt`

- Source candidate: GitHub Actions run `27313765016`.
- Source artifact: `historical-work-id-discovery`.
- Source candidate SHA-256:
  `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`.
- Batch index: 1 of 68.
- Batch size: 500 work IDs.
- First work ID: `act_imperial_1539_1`.
- Last work ID: `act_local_1889_22`.
- Canonical line-normalized batch SHA-256:
  `59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
- Intended use: no-upload validation through `historical_hf_upload.yml` before
  any confirmed incremental historical upload.

Do not claim completeness from this seed. It is the first deterministic batch
from a search-derived candidate inventory that still requires authoritative or
external reconciliation.
