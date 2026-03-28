from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        layout.addWidget(QLabel(description))
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("photo-tools")
        self.resize(960, 640)

        tabs = QTabWidget()
        tabs.addTab(
            PlaceholderPage(
                "批量修改照片时间",
                "阶段 1 占位页。后续在这里实现扫描、预览、确认和执行流程。",
            ),
            "时间修改",
        )
        tabs.addTab(
            PlaceholderPage(
                "按成片保留原片",
                "阶段 1 占位页。后续在这里实现匹配预览、删除策略和执行流程。",
            ),
            "原片筛选",
        )

        self.setCentralWidget(tabs)

