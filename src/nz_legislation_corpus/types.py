from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FormatLink:
    type: str
    url: str


@dataclass
class SyncStats:
    works_checked: int = 0
    versions_checked: int = 0
    records_added: int = 0
    records_changed: int = 0
    records_unchanged: int = 0
    records_failed: int = 0
    records_deferred: int = 0
    parquet_files_written: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "works_checked": self.works_checked,
            "versions_checked": self.versions_checked,
            "records_added": self.records_added,
            "records_changed": self.records_changed,
            "records_unchanged": self.records_unchanged,
            "records_failed": self.records_failed,
            "records_deferred": self.records_deferred,
            "parquet_files_written": self.parquet_files_written,
            "warnings": self.warnings,
        }
