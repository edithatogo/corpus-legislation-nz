---
license: other
language:
- en
tags:
- new-zealand
- legislation
- law
- legal-corpus
- parquet
- xet
pretty_name: New Zealand Legislation Corpus
---

# New Zealand Legislation Corpus

## Summary

This dataset is intended to contain machine-readable New Zealand legislation records collected through the official New Zealand Legislation API and published as optimized Parquet shards for live use. Coverage is not yet proven complete.

## Source provenance

Records include source URLs, API URLs, format URLs, hashes, scrape timestamps, and pipeline version metadata.

## Data fields

Core fields are documented in `docs/data_dictionary.md`. They include:

- `stable_id`
- `work_id`
- `version_id`
- `title`
- `legislation_type`
- `legislation_status`
- `source_url`
- `api_url`
- `xml_url`
- `html_url`
- `pdf_url`
- `text`
- `text_sha256`
- `source_hash`

## Intended use

- legal information retrieval
- statutory text search
- legal NLP experiments
- reproducible public-law data analysis
- annual comparison of statutory change

## Limitations

- Corpus completeness is not yet proven. The current API-first pipeline depends on the configured discovery strategy, and search-based discovery must be reconciled against an authoritative inventory before any full-coverage claim.
- Text extraction is intentionally conservative and may not preserve all legal structure.
- Incorporated-by-reference material, third-party material, agency website text, logos, emblems, and non-legislative linked content may not be included or may have different rights.
- This dataset is not legal advice.

## Loading examples

```python
from datasets import load_dataset

ds = load_dataset("edithatogo/nz-legislation-corpus", split="train", streaming=True)
for row in ds.take(1):
    print(row["title"])
```

```python
import pyarrow.dataset as ds

dataset = ds.dataset("data/parquet", format="parquet", partitioning="hive")
table = dataset.to_table(columns=["title", "legislation_type", "text"])
```

```sql
-- DuckDB example
SELECT title, legislation_type
FROM read_parquet('hf://datasets/edithatogo/nz-legislation-corpus/parquet/**/*.parquet')
LIMIT 10;
```

## Update cadence

The live Hugging Face dataset is intended for daily or regular updates. DOI-backed snapshots are intended for annual Zenodo archival releases.

## Citation

For academic or fixed-version citation, cite the Zenodo snapshot DOI: `10.5281/zenodo.20592540`. For live use, cite the Hugging Face repository, access date, and the manifest hash from `manifests/latest_manifest.json`.

## Licensing and legal caveat

The code that builds this dataset is licensed separately in the source repository. This dataset card does not relicense legislation text or third-party source material. Check the official New Zealand Legislation copyright page and your own institution's policies before redistributing or relying on the dataset. This dataset is provided for information and research support, not legal advice.
