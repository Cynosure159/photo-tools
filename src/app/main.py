from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VENV = PROJECT_ROOT / ".venv"


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


def main() -> int:
    ensure_project_venv()

    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError(
            "PyQt6 is not installed in the active .venv. "
            "Run `pip install -r requirements.txt`."
        ) from exc

    from src.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("photo-tools")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
