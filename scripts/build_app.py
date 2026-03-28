from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PROJECT_ROOT / "src" / "app" / "main.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
PYINSTALLER_CONFIG_DIR = PROJECT_ROOT / ".pyinstaller"

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


def build_output_name(target_platform: str, target_arch: str) -> str:
    return f"photo-tools-{target_platform}-{target_arch}"


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


def main() -> int:
    args = parse_args()
    validate_target(args.target_platform, args.target_arch)

    environment = os.environ.copy()
    environment["PYINSTALLER_CONFIG_DIR"] = str(PYINSTALLER_CONFIG_DIR)
    output_name = build_output_name(args.target_platform, args.target_arch)
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
        output_name,
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
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
