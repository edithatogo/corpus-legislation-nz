# Researcher quickstart

This guide is for downstream users who want to inspect the published corpus without cloning raw XML or downloading the whole repository.

## Current publication status

The live Hugging Face dataset is available at `edithatogo/nz-legislation-corpus`. Cite live results with the Hugging Face dataset URL, access date, and manifest hash.

Coverage is not proven complete until the dataset has been reconciled against an authoritative inventory.

## Query Parquet from Hugging Face with DuckDB

DuckDB can read Parquet files directly from Hugging Face paths:

```sql
INSTALL httpfs;
LOAD httpfs;

SELECT
  title,
  legislation_type,
  legislation_status,
  year
FROM read_parquet('hf://datasets/edithatogo/nz-legislation-corpus/parquet/**/*.parquet')
LIMIT 20;
```

Count records by legislation type and year:

```sql
INSTALL httpfs;
LOAD httpfs;

SELECT
  legislation_type,
  year,
  count(*) AS records
FROM read_parquet('hf://datasets/edithatogo/nz-legislation-corpus/parquet/**/*.parquet')
GROUP BY legislation_type, year
ORDER BY year DESC, legislation_type;
```

## Query local Parquet with PyArrow

After downloading or generating `data/parquet`, use PyArrow:

```python
import pyarrow.dataset as ds
import pyarrow as pa

partitioning = ds.partitioning(
    pa.schema([
        ("legislation_type", pa.string()),
        ("year", pa.int64()),
    ]),
    flavor="hive",
)
dataset = ds.dataset("data/parquet", format="parquet", partitioning=partitioning)
table = dataset.to_table(columns=["stable_id", "title", "legislation_type", "year"])
print(table.to_pandas().head(20))
```

## Minimal local smoke corpus

For tooling checks without network access:

```bash
ARCHIVE_CREATORS_JSON='[{"name":"Local Smoke Test"}]' uv run nzlc smoke-fixture --output-dir data
NZLC_OUTPUT_DIR=data uv run nzlc validate
NZLC_OUTPUT_DIR=data uv run nzlc manifest
NZLC_OUTPUT_DIR=data uv run nzlc coverage-report
```

Then query `data/parquet` with the PyArrow example above.

## Sample split policy

A separate public sample split should be added only after the live Hugging Face dataset exists. Until then, the repository keeps only tiny fixtures for tests and avoids publishing a sample that could be mistaken for coverage evidence.
