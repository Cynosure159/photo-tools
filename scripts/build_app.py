from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "photo-tools"
ENTRYPOINT = PROJECT_ROOT / "src" / "app" / "main.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
PYINSTALLER_CONFIG_DIR = PROJECT_ROOT / ".pyinstaller"
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"

SUPPORTED_TARGETS = {
    "macos": {"arm64", "x86_64"},
    "windows": {"x86"},
}


def detect_default_target() -> tuple[str, str]:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        if machine in {"arm64", "aarch64"}:
            return ("macos", "arm64")
        if machine in {"x86_64", "amd64"}:
            return ("macos", "x86_64")
    elif system == "Windows":
        return ("windows", "x86")

    raise RuntimeError(
        f"Unsupported host platform for app builds: {system} / {machine}"
    )


def parse_args() -> argparse.Namespace:
    default_platform, default_arch = detect_default_target()
    parser = argparse.ArgumentParser(
        description="Build photo-tools desktop application packages.",
    )
    parser.add_argument(
        "--platform",
        dest="target_platform",
        choices=sorted(SUPPORTED_TARGETS),
        default=default_platform,
        help="Target platform for the build output.",
    )
    parser.add_argument(
        "--arch",
        dest="target_arch",
        default=default_arch,
        help="Target architecture for the build output.",
    )
    return parser.parse_args()


def validate_target(target_platform: str, target_arch: str) -> None:
    supported_arches = SUPPORTED_TARGETS.get(target_platform)
    if supported_arches is None or target_arch not in supported_arches:
        raise RuntimeError(
            f"Unsupported build target: {target_platform}/{target_arch}. "
            f"Supported targets: {SUPPORTED_TARGETS}."
        )


def target_architecture_args(target_platform: str, target_arch: str) -> list[str]:
    if target_platform != "macos":
        return []
    return ["--target-architecture", target_arch]


def icon_args(target_platform: str) -> list[str]:
    icon_name = {
        "macos": "app-icon.icns",
        "windows": "app-icon.ico",
    }[target_platform]
    return ["--icon", str(ICONS_DIR / icon_name)]


def data_args() -> list[str]:
    source = ICONS_DIR / "app-icon.png"
    return ["--add-data", f"{source}{os.pathsep}assets/icons"]


def main() -> int:
    args = parse_args()
    validate_target(args.target_platform, args.target_arch)

    environment = os.environ.copy()
    environment["PYINSTALLER_CONFIG_DIR"] = str(PYINSTALLER_CONFIG_DIR)
    build_dir = BUILD_DIR / f"{args.target_platform}-{args.target_arch}"
    dist_dir = DIST_DIR / f"{args.target_platform}-{args.target_arch}"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        *icon_args(args.target_platform),
        *data_args(),
        *target_architecture_args(args.target_platform, args.target_arch),
        str(ENTRYPOINT),
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
