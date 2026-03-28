from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from src.infrastructure.photo_time import (
    read_photo_timestamps,
    scan_photo_files,
    set_created_time,
    set_modified_time,
    set_taken_time,
    supports_created_time_write,
    supports_taken_time_write,
)
from src.models.time_shift import (
    TimeShiftExecutionRecord,
    TimeShiftExecutionResult,
    TimeShiftPreviewRecord,
    TimeShiftRequest,
)


def build_time_shift_request(
    *,
    selected_files: list[Path],
    selected_directory: Path | None,
    offset_days: int,
    offset_hours: int,
    offset_minutes: int,
    offset_seconds: int,
    update_created_at: bool,
    update_modified_at: bool,
    update_taken_at: bool,
) -> TimeShiftRequest:
    if selected_files:
        paths = tuple(selected_files)
    else:
        assert selected_directory is not None
        paths = tuple(scan_photo_files(selected_directory))

    return TimeShiftRequest(
        paths=paths,
        offset=timedelta(
            days=offset_days,
            hours=offset_hours,
            minutes=offset_minutes,
            seconds=offset_seconds,
        ),
        update_created_at=update_created_at,
        update_modified_at=update_modified_at,
        update_taken_at=update_taken_at,
    )


def generate_preview(request: TimeShiftRequest) -> list[TimeShiftPreviewRecord]:
    return [_build_preview_record(path, request) for path in request.paths]


def execute_time_shift(
    request: TimeShiftRequest,
    preview_records: list[TimeShiftPreviewRecord],
) -> TimeShiftExecutionResult:
    preview_by_path = {record.path: record for record in preview_records}
    execution_records: list[TimeShiftExecutionRecord] = []
    succeeded = 0
    failed = 0
    skipped = 0

    for path in request.paths:
        preview_record = preview_by_path[path]
        if preview_record.status == "不可执行":
            execution_records.append(
                TimeShiftExecutionRecord(
                    path=path,
                    status="跳过",
                    message=preview_record.message,
                )
            )
            skipped += 1
            continue

        messages: list[str] = []
        errors: list[str] = []

        _apply_time_update(
            should_update=request.update_taken_at,
            value=preview_record.after_taken_at,
            path=path,
            success_message="拍摄时间已写入",
            failure_prefix="拍摄时间失败",
            writer=set_taken_time,
            messages=messages,
            errors=errors,
        )
        _apply_time_update(
            should_update=request.update_modified_at,
            value=preview_record.after_modified_at,
            path=path,
            success_message="修改时间已写入",
            failure_prefix="修改时间失败",
            writer=set_modified_time,
            messages=messages,
            errors=errors,
        )
        _apply_time_update(
            should_update=request.update_created_at,
            value=preview_record.after_created_at,
            path=path,
            success_message="创建时间已写入",
            failure_prefix="创建时间失败",
            writer=set_created_time,
            messages=messages,
            errors=errors,
        )

        if errors and messages:
            execution_records.append(
                TimeShiftExecutionRecord(
                    path=path,
                    status="部分成功",
                    message="；".join(messages + errors),
                )
            )
            failed += 1
        elif errors:
            execution_records.append(
                TimeShiftExecutionRecord(
                    path=path,
                    status="失败",
                    message="；".join(errors),
                )
            )
            failed += 1
        else:
            execution_records.append(
                TimeShiftExecutionRecord(
                    path=path,
                    status="成功",
                    message="；".join(messages) or "已按预览结果完成写入。",
                )
            )
            succeeded += 1

    return TimeShiftExecutionResult(
        total=len(request.paths),
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
        records=tuple(execution_records),
    )


def _build_preview_record(
    path: Path, request: TimeShiftRequest
) -> TimeShiftPreviewRecord:
    try:
        timestamps = read_photo_timestamps(path)
    except Exception as exc:
        return TimeShiftPreviewRecord(
            path=path,
            name=path.name,
            before_created_at=None,
            after_created_at=None,
            before_modified_at=None,
            after_modified_at=None,
            before_taken_at=None,
            after_taken_at=None,
            status="不可执行",
            message=f"无法读取文件时间信息：{exc}",
        )

    messages: list[str] = []
    executable = False

    before_created_at = timestamps.created_at
    after_created_at: datetime | None = None
    if request.update_created_at:
        if before_created_at is None:
            messages.append("无可读取的创建时间")
        elif supports_created_time_write():
            after_created_at = before_created_at + request.offset
            executable = True
        else:
            messages.append("当前平台暂不支持写入创建时间")

    before_modified_at = timestamps.modified_at
    after_modified_at: datetime | None = None
    if request.update_modified_at:
        after_modified_at = before_modified_at + request.offset
        executable = True

    before_taken_at = timestamps.taken_at
    after_taken_at: datetime | None = None
    if request.update_taken_at:
        if before_taken_at is None:
            messages.append("无 EXIF 拍摄时间")
        elif supports_taken_time_write(path):
            after_taken_at = before_taken_at + request.offset
            executable = True
        else:
            messages.append("当前文件格式暂不支持写入 EXIF 拍摄时间")

    status = "待执行" if executable else "不可执行"
    message = "；".join(messages) if messages else "可按当前偏移执行时间修改。"
    return TimeShiftPreviewRecord(
        path=path,
        name=path.name,
        before_created_at=before_created_at,
        after_created_at=after_created_at,
        before_modified_at=before_modified_at,
        after_modified_at=after_modified_at,
        before_taken_at=before_taken_at,
        after_taken_at=after_taken_at,
        status=status,
        message=message,
    )


def _apply_time_update(
    *,
    should_update: bool,
    value: datetime | None,
    path: Path,
    success_message: str,
    failure_prefix: str,
    writer,
    messages: list[str],
    errors: list[str],
) -> None:
    if not should_update or value is None:
        return

    try:
        writer(path, value)
        messages.append(success_message)
    except Exception as exc:  # pragma: no cover
        errors.append(f"{failure_prefix}：{exc}")
