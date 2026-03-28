from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from src.ui.raw_cleanup_page import RawCleanupPage
from src.ui.time_shift_page import TimeShiftPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("photo-tools")
        self.resize(1280, 800)

        tabs = QTabWidget()
        tabs.addTab(TimeShiftPage(), "时间修改")
        tabs.addTab(RawCleanupPage(), "原片筛选")
        self.setCentralWidget(tabs)
