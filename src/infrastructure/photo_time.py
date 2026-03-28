from __future__ import annotations

import ctypes
import os
import platform
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import piexif

SUPPORTED_PHOTO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".tif",
    ".tiff",
    ".arw",
    ".cr2",
    ".nef",
    ".dng",
}

EXIF_WRITABLE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff"}


@dataclass(frozen=True)
class PhotoTimestamps:
    created_at: datetime | None
    modified_at: datetime | None
    taken_at: datetime | None


def is_supported_photo(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_PHOTO_EXTENSIONS


def scan_photo_files(directory: Path) -> list[Path]:
    photo_files = [
        path
        for path in directory.iterdir()
        if path.is_file() and is_supported_photo(path)
    ]
    return sorted(photo_files, key=lambda item: item.name.lower())


def read_photo_timestamps(path: Path) -> PhotoTimestamps:
    stat_result = path.stat()
    created_at = _read_created_time(stat_result)
    modified_at = datetime.fromtimestamp(stat_result.st_mtime)
    taken_at = _read_exif_taken_at(path)
    return PhotoTimestamps(
        created_at=created_at,
        modified_at=modified_at,
        taken_at=taken_at,
    )


def supports_created_time_write() -> bool:
    return platform.system() == "Windows"


def supports_taken_time_write(path: Path) -> bool:
    return path.suffix.lower() in EXIF_WRITABLE_EXTENSIONS


def set_modified_time(path: Path, value: datetime) -> None:
    timestamp = value.timestamp()
    stat_result = path.stat()
    os.utime(path, (stat_result.st_atime, timestamp))


def set_created_time(path: Path, value: datetime) -> None:
    if not supports_created_time_write():
        raise NotImplementedError("当前平台暂不支持写入创建时间。")

    _set_windows_creation_time(path, value)


def set_taken_time(path: Path, value: datetime) -> None:
    if not supports_taken_time_write(path):
        raise NotImplementedError("当前文件格式暂不支持写入 EXIF 拍摄时间。")

    try:
        exif_dict = piexif.load(str(path))
    except piexif.InvalidImageDataError:
        exif_dict = _empty_exif_dict()

    exif_bytes = _build_exif_bytes(exif_dict, value)
    piexif.insert(exif_bytes, str(path))


def _read_created_time(stat_result: os.stat_result) -> datetime | None:
    if hasattr(stat_result, "st_birthtime"):
        birthtime = stat_result.st_birthtime
        if birthtime is not None:
            return datetime.fromtimestamp(birthtime)
    if platform.system() == "Windows":
        return datetime.fromtimestamp(stat_result.st_ctime)
    return None


def _read_exif_taken_at(path: Path) -> datetime | None:
    try:
        exif_dict = piexif.load(str(path))
    except (piexif.InvalidImageDataError, OSError, ValueError):
        return None

    candidates = [
        exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal),
        exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeDigitized),
        exif_dict.get("0th", {}).get(piexif.ImageIFD.DateTime),
    ]
    for value in candidates:
        parsed = _parse_exif_datetime(value)
        if parsed is not None:
            return parsed
    return None


def _parse_exif_datetime(value: bytes | str | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="ignore")
    else:
        text = value
    try:
        return datetime.strptime(text, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _build_exif_bytes(exif_dict: dict, value: datetime) -> bytes:
    encoded = value.strftime("%Y:%m:%d %H:%M:%S").encode("ascii")
    exif_dict.setdefault("0th", {})
    exif_dict.setdefault("Exif", {})
    exif_dict["0th"][piexif.ImageIFD.DateTime] = encoded
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = encoded
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = encoded
    return piexif.dump(exif_dict)


def _empty_exif_dict() -> dict:
    return {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}


def _set_windows_creation_time(path: Path, value: datetime) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE

    set_file_time = kernel32.SetFileTime
    set_file_time.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    ]
    set_file_time.restype = wintypes.BOOL

    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    file_handle = create_file(
        str(path),
        0x0100,
        0x00000001 | 0x00000002 | 0x00000004,
        None,
        3,
        0x02000000,
        None,
    )
    if file_handle == wintypes.HANDLE(-1).value:
        raise OSError(ctypes.get_last_error(), "无法打开文件以写入创建时间。")

    try:
        file_time = _datetime_to_filetime(value)
        if not set_file_time(file_handle, ctypes.byref(file_time), None, None):
            raise OSError(ctypes.get_last_error(), "写入创建时间失败。")
    finally:
        close_handle(file_handle)


def _datetime_to_filetime(value: datetime) -> wintypes.FILETIME:
    if value.tzinfo is None:
        utc_value = value.astimezone()
    else:
        utc_value = value.astimezone(timezone.utc)
    unix_time = utc_value.timestamp()
    filetime = int((unix_time + 11644473600) * 10_000_000)
    return wintypes.FILETIME(filetime & 0xFFFFFFFF, filetime >> 32)
