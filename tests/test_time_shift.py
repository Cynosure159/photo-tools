from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import piexif
import pytest
from PIL import Image

from src.infrastructure.photo_time import read_photo_timestamps
from src.tasks.time_shift import (
    build_time_shift_request,
    execute_time_shift,
    generate_preview,
)


def test_preview_computes_modified_and_taken_offsets(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.jpg"
    original_taken_at = datetime(2024, 5, 1, 12, 30, 0)
    create_image(image_path, original_taken_at)

    original_modified_at = datetime(2024, 5, 2, 8, 0, 0)
    set_modified_time(image_path, original_modified_at)

    request = build_request(
        image_path=image_path,
        offset=timedelta(days=1, hours=2, seconds=30),
    )

    preview = generate_preview(request)

    assert len(preview) == 1
    assert preview[0].status == "待执行"
    assert preview[0].after_modified_at == (
        original_modified_at + timedelta(days=1, hours=2, seconds=30)
    )
    assert preview[0].after_taken_at == (
        original_taken_at + timedelta(days=1, hours=2, seconds=30)
    )


def test_execute_updates_modified_and_taken_times(tmp_path: Path) -> None:
    image_path = tmp_path / "execute.jpg"
    original_taken_at = datetime(2024, 6, 1, 7, 15, 0)
    create_image(image_path, original_taken_at)

    original_modified_at = datetime(2024, 6, 2, 9, 0, 0)
    set_modified_time(image_path, original_modified_at)

    request = build_request(
        image_path=image_path,
        offset=timedelta(hours=3, minutes=5),
    )

    preview = generate_preview(request)
    result = execute_time_shift(request, preview)
    timestamps = read_photo_timestamps(image_path)

    assert result.succeeded == 1
    assert result.failed == 0
    assert result.skipped == 0
    assert timestamps.taken_at is not None
    assert timestamps.modified_at.replace(microsecond=0) == (
        original_modified_at + timedelta(hours=3, minutes=5)
    ).replace(microsecond=0)
    assert timestamps.taken_at == original_taken_at + timedelta(hours=3, minutes=5)


def test_build_request_preserves_day_offset_components(tmp_path: Path) -> None:
    image_path = tmp_path / "offset.jpg"
    original_taken_at = datetime(2024, 7, 1, 10, 0, 0)
    create_image(image_path, original_taken_at)

    offset = timedelta(days=1, hours=2, minutes=30, seconds=45)
    request = build_request(image_path=image_path, offset=offset)

    assert request.offset == offset

    preview = generate_preview(request)

    assert preview[0].after_taken_at == original_taken_at + offset


def test_execute_reports_writer_failure_without_aborting_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_path = tmp_path / "first.jpg"
    second_path = tmp_path / "second.jpg"
    original_taken_at = datetime(2024, 8, 1, 9, 0, 0)
    create_image(first_path, original_taken_at)
    create_image(second_path, original_taken_at)

    request = build_time_shift_request(
        selected_files=[first_path, second_path],
        selected_directory=None,
        offset_days=0,
        offset_hours=1,
        offset_minutes=0,
        offset_seconds=0,
        update_created_at=False,
        update_modified_at=True,
        update_taken_at=False,
    )
    preview = generate_preview(request)

    writer = Mock(side_effect=[PermissionError("只读文件"), None])
    monkeypatch.setattr("src.tasks.time_shift.set_modified_time", writer)

    result = execute_time_shift(request, preview)

    assert result.total == 2
    assert result.succeeded == 1
    assert result.failed == 1
    assert result.skipped == 0
    assert writer.call_count == 2
    assert result.records[0].status == "失败"
    assert "修改时间失败" in result.records[0].message
    assert result.records[1].status == "成功"


def create_image(path: Path, taken_at: datetime) -> None:
    image = Image.new("RGB", (16, 16), color="red")
    encoded_taken_at = taken_at.strftime("%Y:%m:%d %H:%M:%S").encode("ascii")
    exif_bytes = piexif.dump(
        {
            "0th": {piexif.ImageIFD.DateTime: encoded_taken_at},
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: encoded_taken_at,
                piexif.ExifIFD.DateTimeDigitized: encoded_taken_at,
            },
            "GPS": {},
            "1st": {},
            "thumbnail": None,
        }
    )
    image.save(path, exif=exif_bytes)


def set_modified_time(path: Path, value: datetime) -> None:
    timestamp = value.timestamp()
    os.utime(path, (timestamp, timestamp))


def build_request(*, image_path: Path, offset: timedelta):
    total_offset_seconds = int(offset.total_seconds())
    sign = -1 if total_offset_seconds < 0 else 1
    absolute_seconds = abs(total_offset_seconds)
    total_days, remainder = divmod(absolute_seconds, 24 * 60 * 60)
    total_hours, remainder = divmod(remainder, 60 * 60)
    total_minutes, total_seconds = divmod(remainder, 60)
    return build_time_shift_request(
        selected_files=[image_path],
        selected_directory=None,
        offset_days=sign * total_days,
        offset_hours=sign * total_hours,
        offset_minutes=sign * total_minutes,
        offset_seconds=sign * total_seconds,
        update_created_at=False,
        update_modified_at=True,
        update_taken_at=True,
    )
