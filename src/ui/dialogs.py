from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget


def show_info(parent: QWidget, title: str, message: str) -> None:
    QMessageBox.information(parent, title, message)


def show_warning(parent: QWidget, title: str, message: str) -> None:
    QMessageBox.warning(parent, title, message)


def confirm_time_shift(parent: QWidget, summary: str) -> bool:
    return (
        QMessageBox.question(
            parent,
            "确认执行时间修改",
            f"请确认将按预览结果批量修改照片时间。\n\n{summary}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )


def confirm_cleanup(parent: QWidget, summary: str, permanent_delete: bool) -> bool:
    warning = (
        "你选择了永久删除模式。该操作不可恢复，请再次确认。"
        if permanent_delete
        else "你选择了移动到回收站模式。"
    )

    return (
        QMessageBox.question(
            parent,
            "确认执行原片清理",
            f"{warning}\n\n{summary}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )
