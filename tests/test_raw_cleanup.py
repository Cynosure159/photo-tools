from __future__ import annotations

from pathlib import Path

import pytest

from src.tasks.raw_cleanup import (
    build_raw_cleanup_request,
    execute_cleanup,
    generate_cleanup_preview,
)


def test_preview_matches_by_case_insensitive_stem(tmp_path: Path) -> None:
    selected_dir, source_dir = _make_cleanup_directories(tmp_path)
    (selected_dir / "IMG_0001.JPG").write_bytes(b"selected")
    (source_dir / "img_0001.ARW").write_bytes(b"keep")
    (source_dir / "IMG_9999.NEF").write_bytes(b"cleanup")
    # `.xmp` 不在 SUPPORTED_PHOTO_EXTENSIONS 中，因此不会计入 source_count。
    (source_dir / "IMG_0001.xmp").write_bytes(b"sidecar")

    preview = generate_cleanup_preview(
        make_raw_cleanup_request(
            selected_dir=selected_dir,
            source_dir=source_dir,
            delete_mode="trash",
        )
    )

    assert preview.selected_count == 1
    assert preview.source_count == 2
    assert preview.keep_count == 1
    assert preview.process_count == 1
    assert [
        (record.name, record.matched, record.planned_action)
        for record in preview.records
    ] == [
        ("img_0001.ARW", True, "保留"),
        ("IMG_9999.NEF", False, "移动到回收站"),
    ]


def test_execute_cleanup_trashes_unmatched_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected_dir, source_dir = _make_cleanup_directories(tmp_path)
    (selected_dir / "IMG_0001.JPG").write_bytes(b"selected")
    keep_path = source_dir / "IMG_0001.ARW"
    delete_path = source_dir / "IMG_9999.ARW"
    keep_path.write_bytes(b"keep")
    delete_path.write_bytes(b"delete")

    request = make_raw_cleanup_request(
        selected_dir=selected_dir,
        source_dir=source_dir,
        delete_mode="trash",
    )
    preview = generate_cleanup_preview(request)

    calls: list[str] = []
    monkeypatch.setattr("src.tasks.raw_cleanup.send2trash", calls.append)

    result = execute_cleanup(request, preview)

    assert calls == [str(delete_path)]
    assert keep_path.exists()
    assert delete_path.exists()
    assert result.kept == 1
    assert result.processed == 1
    assert result.succeeded == 1
    assert result.failed == 0


def test_execute_cleanup_permanently_deletes_unmatched_files(tmp_path: Path) -> None:
    selected_dir, source_dir = _make_cleanup_directories(tmp_path)
    (selected_dir / "IMG_0001.JPG").write_bytes(b"selected")
    keep_path = source_dir / "IMG_0001.ARW"
    delete_path = source_dir / "IMG_9999.ARW"
    keep_path.write_bytes(b"keep")
    delete_path.write_bytes(b"delete")

    request = make_raw_cleanup_request(
        selected_dir=selected_dir,
        source_dir=source_dir,
        delete_mode="permanent",
    )
    preview = generate_cleanup_preview(request)
    result = execute_cleanup(request, preview)

    assert keep_path.exists()
    assert not delete_path.exists()
    assert result.kept == 1
    assert result.processed == 1
    assert result.succeeded == 1
    assert result.failed == 0


def make_raw_cleanup_request(
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


def _make_cleanup_directories(tmp_path: Path) -> tuple[Path, Path]:
    selected_dir = tmp_path / "selected"
    source_dir = tmp_path / "source"
    selected_dir.mkdir()
    source_dir.mkdir()
    return selected_dir, source_dir
