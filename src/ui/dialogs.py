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
        "你选择了永久删除模式。该操作不可恢复，且会直接删除文件，请再次确认。"
        if permanent_delete
        else "你选择了移动到回收站模式。"
    )
    dialog = QMessageBox(parent)
    dialog.setWindowTitle("确认执行原片清理")
    dialog.setText(f"{warning}\n\n{summary}")
    dialog.setIcon(
        QMessageBox.Icon.Warning if permanent_delete else QMessageBox.Icon.Question
    )
    dialog.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    dialog.setDefaultButton(QMessageBox.StandardButton.No)
    return dialog.exec() == QMessageBox.StandardButton.Yes
