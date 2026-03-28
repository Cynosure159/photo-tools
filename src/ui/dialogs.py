from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget


def show_info(parent: QWidget, title: str, message: str) -> None:
    QMessageBox.information(parent, title, message)


def show_warning(parent: QWidget, title: str, message: str) -> None:
    QMessageBox.warning(parent, title, message)


def confirm_time_shift(parent: QWidget, summary: str) -> bool:
    return _confirm_dialog(
        parent=parent,
        title="确认执行时间修改",
        message=f"请确认将按预览结果批量修改照片时间。\n\n{summary}",
        icon=QMessageBox.Icon.Question,
    )


def confirm_cleanup(parent: QWidget, summary: str, permanent_delete: bool) -> bool:
    if permanent_delete:
        warning = "你选择了永久删除模式。该操作不可恢复，且会直接删除文件，请再次确认。"
        icon = QMessageBox.Icon.Warning
    else:
        warning = "你选择了移动到回收站模式。"
        icon = QMessageBox.Icon.Question

    return _confirm_dialog(
        parent=parent,
        title="确认执行原片清理",
        message=f"{warning}\n\n{summary}",
        icon=icon,
    )


def _confirm_dialog(
    *,
    parent: QWidget,
    title: str,
    message: str,
    icon: QMessageBox.Icon,
) -> bool:
    dialog = QMessageBox(parent)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    dialog.setIcon(icon)
    dialog.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    dialog.setDefaultButton(QMessageBox.StandardButton.No)
    return dialog.exec() == QMessageBox.StandardButton.Yes
