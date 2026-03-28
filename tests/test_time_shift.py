from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import piexif
from PIL import Image

from src.infrastructure.photo_time import read_photo_timestamps
from src.tasks.time_shift import (
    build_time_shift_request,
    execute_time_shift,
    generate_preview,
)


class TimeShiftTaskTests(unittest.TestCase):
    def test_preview_computes_modified_and_taken_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "sample.jpg"
            original_taken_at = datetime(2024, 5, 1, 12, 30, 0)
            self._create_image(image_path, original_taken_at)

            original_modified_at = datetime(2024, 5, 2, 8, 0, 0)
            self._set_modified_time(image_path, original_modified_at)

            request = self._build_request(
                image_path=image_path,
                offset=timedelta(days=1, hours=2, seconds=30),
            )

            preview = generate_preview(request)

            self.assertEqual(len(preview), 1)
            self.assertEqual(preview[0].status, "待执行")
            self.assertEqual(
                preview[0].after_modified_at,
                original_modified_at + timedelta(days=1, hours=2, seconds=30),
            )
            self.assertEqual(
                preview[0].after_taken_at,
                original_taken_at + timedelta(days=1, hours=2, seconds=30),
            )

    def test_execute_updates_modified_and_taken_times(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "execute.jpg"
            original_taken_at = datetime(2024, 6, 1, 7, 15, 0)
            self._create_image(image_path, original_taken_at)

            original_modified_at = datetime(2024, 6, 2, 9, 0, 0)
            self._set_modified_time(image_path, original_modified_at)

            request = self._build_request(
                image_path=image_path,
                offset=timedelta(hours=3, minutes=5),
            )

            preview = generate_preview(request)
            result = execute_time_shift(request, preview)
            timestamps = read_photo_timestamps(image_path)

            self.assertEqual(result.succeeded, 1)
            self.assertEqual(result.failed, 0)
            self.assertEqual(result.skipped, 0)
            self.assertIsNotNone(timestamps.taken_at)
            self.assertEqual(
                timestamps.modified_at.replace(microsecond=0),
                (original_modified_at + timedelta(hours=3, minutes=5)).replace(
                    microsecond=0
                ),
            )
            self.assertEqual(
                timestamps.taken_at,
                original_taken_at + timedelta(hours=3, minutes=5),
            )

    def _create_image(self, path: Path, taken_at: datetime) -> None:
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

    def _set_modified_time(self, path: Path, value: datetime) -> None:
        timestamp = value.timestamp()
        os.utime(path, (timestamp, timestamp))

    def _build_request(self, *, image_path: Path, offset: timedelta):
        return build_time_shift_request(
            selected_files=[image_path],
            selected_directory=None,
            offset_days=offset.days,
            offset_hours=offset.seconds // 3600,
            offset_minutes=(offset.seconds % 3600) // 60,
            offset_seconds=offset.seconds % 60,
            update_created_at=False,
            update_modified_at=True,
            update_taken_at=True,
        )


if __name__ == "__main__":
    unittest.main()
