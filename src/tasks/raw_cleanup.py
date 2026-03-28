from __future__ import annotations

from pathlib import Path

from send2trash import send2trash

from src.infrastructure.photo_time import scan_photo_files
from src.models.raw_cleanup import (
    RawCleanupExecutionRecord,
    RawCleanupExecutionResult,
    RawCleanupPreview,
    RawCleanupPreviewRecord,
    RawCleanupRequest,
)

DELETE_MODE_LABELS = {
    "trash": "移动到回收站",
    "permanent": "永久删除",
}


def build_raw_cleanup_request(
    *, selected_dir: Path, source_dir: Path, delete_mode: str
) -> RawCleanupRequest:
    return RawCleanupRequest(
        selected_dir=selected_dir,
        source_dir=source_dir,
        delete_mode=delete_mode,
    )


def generate_cleanup_preview(request: RawCleanupRequest) -> RawCleanupPreview:
    selected_files = scan_photo_files(request.selected_dir)
    source_files = scan_photo_files(request.source_dir)
    selected_stems = _build_selected_stems(selected_files)
    records = tuple(
        _build_preview_record(
            path=path,
            selected_stems=selected_stems,
            delete_mode=request.delete_mode,
        )
        for path in source_files
    )
    keep_count = _count_matched_records(records)
    process_count = len(records) - keep_count

    return RawCleanupPreview(
        selected_count=len(selected_files),
        source_count=len(source_files),
        keep_count=keep_count,
        process_count=process_count,
        records=records,
    )


def execute_cleanup(
    request: RawCleanupRequest,
    preview: RawCleanupPreview,
) -> RawCleanupExecutionResult:
    execution_records: list[RawCleanupExecutionRecord] = []
    kept = 0
    processed = 0
    succeeded = 0
    failed = 0

    for record in preview.records:
        if record.matched:
            execution_records.append(
                RawCleanupExecutionRecord(
                    path=record.path,
                    status="保留",
                    message=record.message,
                )
            )
            kept += 1
            continue

        processed += 1
        try:
            _delete_path(record.path, request.delete_mode)
            execution_records.append(
                RawCleanupExecutionRecord(
                    path=record.path,
                    status="成功",
                    message=f"已{record.planned_action}。",
                )
            )
            succeeded += 1
        except Exception as exc:  # pragma: no cover
            execution_records.append(
                RawCleanupExecutionRecord(
                    path=record.path,
                    status="失败",
                    message=f"{record.planned_action}失败：{exc}",
                )
            )
            failed += 1

    return RawCleanupExecutionResult(
        total=len(preview.records),
        kept=kept,
        processed=processed,
        succeeded=succeeded,
        failed=failed,
        records=tuple(execution_records),
    )


def _build_preview_message(path: Path, matched: bool) -> str:
    if matched:
        return f"文件名主体 {path.stem} 已在成片目录中匹配。"
    return f"文件名主体 {path.stem} 未在成片目录中匹配。"


def _build_preview_record(
    *,
    path: Path,
    selected_stems: set[str],
    delete_mode: str,
) -> RawCleanupPreviewRecord:
    matched = path.stem.casefold() in selected_stems
    planned_action = "保留" if matched else _delete_action_label(delete_mode)
    return RawCleanupPreviewRecord(
        path=path,
        name=path.name,
        stem=path.stem,
        matched=matched,
        planned_action=planned_action,
        message=_build_preview_message(path, matched),
    )


def _build_selected_stems(paths: list[Path]) -> set[str]:
    return {path.stem.casefold() for path in paths}


def _count_matched_records(records: tuple[RawCleanupPreviewRecord, ...]) -> int:
    return sum(record.matched for record in records)


def _delete_action_label(delete_mode: str) -> str:
    try:
        return DELETE_MODE_LABELS[delete_mode]
    except KeyError as exc:
        raise ValueError(f"不支持的删除模式：{delete_mode}") from exc


def _delete_path(path: Path, delete_mode: str) -> None:
    if delete_mode == "trash":
        send2trash(str(path))
        return
    if delete_mode == "permanent":
        path.unlink()
        return
    raise ValueError(f"不支持的删除模式：{delete_mode}")
