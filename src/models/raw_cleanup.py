from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawCleanupRequest:
    selected_dir: Path
    source_dir: Path
    delete_mode: str


@dataclass(frozen=True)
class RawCleanupPreviewRecord:
    path: Path
    name: str
    stem: str
    matched: bool
    planned_action: str
    message: str


@dataclass(frozen=True)
class RawCleanupPreview:
    selected_count: int
    source_count: int
    keep_count: int
    process_count: int
    records: tuple[RawCleanupPreviewRecord, ...]


@dataclass(frozen=True)
class RawCleanupExecutionRecord:
    path: Path
    status: str
    message: str


@dataclass(frozen=True)
class RawCleanupExecutionResult:
    total: int
    kept: int
    processed: int
    succeeded: int
    failed: int
    records: tuple[RawCleanupExecutionRecord, ...]
