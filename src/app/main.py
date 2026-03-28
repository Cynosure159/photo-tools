from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VENV = PROJECT_ROOT / ".venv"
ICON_RELATIVE_PATH = Path("assets/icons/app-icon.png")


def ensure_project_venv() -> None:
    if getattr(sys, "frozen", False):
        return

    current_prefix = Path(sys.prefix).resolve()
    expected_prefix = EXPECTED_VENV.resolve()

    if current_prefix != expected_prefix:
        raise RuntimeError(
            "Python must run inside the project's .venv.\n"
            f"Expected: {expected_prefix}\n"
            f"Current:  {current_prefix}\n"
            "Run `source .venv/bin/activate` first."
        )


def resolve_runtime_path(relative_path: Path) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path  # type: ignore[attr-defined]

    return PROJECT_ROOT / relative_path


def main() -> int:
    ensure_project_venv()

    try:
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError(
            "PyQt6 is not installed in the active .venv. "
            "Run `pip install -r requirements.txt`."
        ) from exc

    from src.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("photo-tools")
    icon_path = resolve_runtime_path(ICON_RELATIVE_PATH)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.setWindowIcon(app.windowIcon())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
