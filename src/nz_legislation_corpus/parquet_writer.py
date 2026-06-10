from __future__ import annotations

import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


def _clean_partition_value(value: Any) -> str:
    text = str(value or "unknown").strip().lower().replace(" ", "_")
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in text) or "unknown"


def _records_to_table(records: list[dict[str, Any]]) -> pa.Table:
    # Drop raw nested metadata from Parquet by default; keep main fields stable and readable.
    cleaned: list[dict[str, Any]] = []
    for record in records:
        item = {k: v for k, v in record.items() if k != "raw_version_metadata"}
        if isinstance(item.get("administering_agencies"), list):
            item["administering_agencies"] = [str(x) for x in item["administering_agencies"]]
        cleaned.append(item)
    return pa.Table.from_pylist(cleaned)


def write_partitioned_parquet(
    records: list[dict[str, Any]],
    output_dir: Path,
    *,
    records_per_file: int = 1000,
    overwrite: bool = True,
) -> list[Path]:
    """Write deterministic, partitioned, optimized Parquet files.

    We prefer one deterministic set of files per legislation_type/year partition. Rewrites are
    acceptable because Hugging Face Xet + PyArrow CDC should deduplicate unchanged chunks.
    """
    output_dir = Path(output_dir)
    if overwrite and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        leg_type = _clean_partition_value(record.get("legislation_type"))
        year = _clean_partition_value(record.get("year") or "unknown")
        grouped[(leg_type, year)].append(record)

    written: list[Path] = []
    for (leg_type, year), group in sorted(grouped.items()):
        group = sorted(
            group, key=lambda r: (str(r.get("stable_id", "")), str(r.get("version_id", "")))
        )
        partition_dir = output_dir / f"legislation_type={leg_type}" / f"year={year}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        for i in range(0, len(group), records_per_file):
            chunk = group[i : i + records_per_file]
            path = partition_dir / f"part-{i // records_per_file:05d}.parquet"
            table = _records_to_table(chunk)
            kwargs: dict[str, Any] = {
                "compression": "zstd",
                "write_page_index": True,
                "use_content_defined_chunking": True,
            }
            try:
                pq.write_table(table, path, **kwargs)
            except TypeError:
                # Older PyArrow may not yet support one or both optimized Parquet args.
                kwargs.pop("use_content_defined_chunking", None)
                try:
                    pq.write_table(table, path, **kwargs)
                except TypeError:
                    kwargs.pop("write_page_index", None)
                    pq.write_table(table, path, **kwargs)
            written.append(path)
    return written


def read_parquet_records(parquet_dir: Path) -> list[dict[str, Any]]:
    dataset = pq.ParquetDataset(parquet_dir)
    table = dataset.read()
    return table.to_pylist()
