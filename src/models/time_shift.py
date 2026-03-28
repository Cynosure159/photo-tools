from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class TimeShiftRequest:
    paths: tuple[Path, ...]
    offset: timedelta
    update_created_at: bool
    update_modified_at: bool
    update_taken_at: bool


@dataclass(frozen=True)
class TimeShiftPreviewRecord:
    path: Path
    name: str
    before_created_at: datetime | None
    after_created_at: datetime | None
    before_modified_at: datetime | None
    after_modified_at: datetime | None
    before_taken_at: datetime | None
    after_taken_at: datetime | None
    status: str
    message: str


@dataclass(frozen=True)
class TimeShiftExecutionRecord:
    path: Path
    status: str
    message: str


@dataclass(frozen=True)
class TimeShiftExecutionResult:
    total: int
    succeeded: int
    failed: int
    skipped: int
    records: tuple[TimeShiftExecutionRecord, ...]
