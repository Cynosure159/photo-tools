from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.tasks.raw_cleanup import (
    build_raw_cleanup_request,
    execute_cleanup,
    generate_cleanup_preview,
)


class RawCleanupTaskTests(unittest.TestCase):
    def _build_request(
        self,
        *,
        selected_dir: Path,
        source_dir: Path,
        delete_mode: str,
    ):
        return build_raw_cleanup_request(
            selected_dir=selected_dir,
            source_dir=source_dir,
            delete_mode=delete_mode,
        )

    def test_preview_matches_by_case_insensitive_stem(self) -> None:
        with tempfile.TemporaryDirectory() as selected_dir_name:
            with tempfile.TemporaryDirectory() as source_dir_name:
                selected_dir = Path(selected_dir_name)
                source_dir = Path(source_dir_name)
                (selected_dir / "IMG_0001.JPG").write_bytes(b"selected")
                (source_dir / "img_0001.ARW").write_bytes(b"keep")
                (source_dir / "IMG_9999.NEF").write_bytes(b"cleanup")
                (source_dir / "IMG_0001.xmp").write_bytes(b"sidecar")

                preview = generate_cleanup_preview(
                    self._build_request(
                        selected_dir=selected_dir,
                        source_dir=source_dir,
                        delete_mode="trash",
                    )
                )

        self.assertEqual(preview.selected_count, 1)
        self.assertEqual(preview.source_count, 2)
        self.assertEqual(preview.keep_count, 1)
        self.assertEqual(preview.process_count, 1)
        self.assertEqual(
            [
                (record.name, record.matched, record.planned_action)
                for record in preview.records
            ],
            [
                ("img_0001.ARW", True, "保留"),
                ("IMG_9999.NEF", False, "移动到回收站"),
            ],
        )

    def test_execute_cleanup_trashes_unmatched_files(self) -> None:
        with tempfile.TemporaryDirectory() as selected_dir_name:
            with tempfile.TemporaryDirectory() as source_dir_name:
                selected_dir = Path(selected_dir_name)
                source_dir = Path(source_dir_name)
                (selected_dir / "IMG_0001.JPG").write_bytes(b"selected")
                keep_path = source_dir / "IMG_0001.ARW"
                delete_path = source_dir / "IMG_9999.ARW"
                keep_path.write_bytes(b"keep")
                delete_path.write_bytes(b"delete")

                request = self._build_request(
                    selected_dir=selected_dir,
                    source_dir=source_dir,
                    delete_mode="trash",
                )
                preview = generate_cleanup_preview(request)

                with patch("src.tasks.raw_cleanup.send2trash") as send2trash_mock:
                    result = execute_cleanup(request, preview)

                send2trash_mock.assert_called_once_with(str(delete_path))
                self.assertTrue(keep_path.exists())
                self.assertTrue(delete_path.exists())
                self.assertEqual(result.kept, 1)
                self.assertEqual(result.processed, 1)
                self.assertEqual(result.succeeded, 1)
                self.assertEqual(result.failed, 0)

    def test_execute_cleanup_permanently_deletes_unmatched_files(self) -> None:
        with tempfile.TemporaryDirectory() as selected_dir_name:
            with tempfile.TemporaryDirectory() as source_dir_name:
                selected_dir = Path(selected_dir_name)
                source_dir = Path(source_dir_name)
                (selected_dir / "IMG_0001.JPG").write_bytes(b"selected")
                keep_path = source_dir / "IMG_0001.ARW"
                delete_path = source_dir / "IMG_9999.ARW"
                keep_path.write_bytes(b"keep")
                delete_path.write_bytes(b"delete")

                request = self._build_request(
                    selected_dir=selected_dir,
                    source_dir=source_dir,
                    delete_mode="permanent",
                )
                preview = generate_cleanup_preview(request)
                result = execute_cleanup(request, preview)

                self.assertTrue(keep_path.exists())
                self.assertFalse(delete_path.exists())

        self.assertEqual(result.kept, 1)
        self.assertEqual(result.processed, 1)
        self.assertEqual(result.succeeded, 1)
        self.assertEqual(result.failed, 0)
