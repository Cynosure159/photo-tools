from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.dialogs import confirm_cleanup, show_info, show_warning


class RawCleanupPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.selected_dir: Path | None = None
        self.source_dir: Path | None = None
        self.preview_ready = False

        root_layout = QVBoxLayout(self)
        root_layout.addWidget(self._build_intro())

        content_layout = QHBoxLayout()
        content_layout.addWidget(self._build_controls(), 1)
        content_layout.addWidget(self._build_preview_area(), 2)
        root_layout.addLayout(content_layout)

        self._refresh_actions()

    def _build_intro(self) -> QGroupBox:
        box = QGroupBox("按成片保留原片")
        layout = QVBoxLayout(box)
        layout.addWidget(
            QLabel(
                "按“成片目录 -> 原片目录 -> 删除策略 -> 预览 -> 二次确认 -> 执行”的流程工作。"
            )
        )
        layout.addWidget(
            QLabel("阶段 2 先搭好高风险操作的交互骨架，真实匹配与删除逻辑留到后续阶段。")
        )
        return box

    def _build_controls(self) -> QGroupBox:
        box = QGroupBox("输入与策略")
        layout = QVBoxLayout(box)

        path_box = QGroupBox("目录选择")
        path_layout = QFormLayout(path_box)

        self.selected_dir_label = QLabel("未选择成片目录")
        self.selected_dir_label.setWordWrap(True)
        self.source_dir_label = QLabel("未选择原片目录")
        self.source_dir_label.setWordWrap(True)

        choose_selected_button = QPushButton("选择成片目录")
        choose_selected_button.clicked.connect(self._choose_selected_dir)
        choose_source_button = QPushButton("选择原片目录")
        choose_source_button.clicked.connect(self._choose_source_dir)
        clear_button = QPushButton("清空目录")
        clear_button.clicked.connect(self._clear_paths)

        path_layout.addRow(choose_selected_button, self.selected_dir_label)
        path_layout.addRow(choose_source_button, self.source_dir_label)
        path_layout.addRow(clear_button)
        layout.addWidget(path_box)

        strategy_box = QGroupBox("处理策略")
        strategy_layout = QFormLayout(strategy_box)
        self.delete_mode_combo = QComboBox()
        self.delete_mode_combo.addItem("移动到回收站（推荐）", "trash")
        self.delete_mode_combo.addItem("永久删除（高风险）", "permanent")
        self.delete_mode_combo.currentIndexChanged.connect(self._on_parameters_changed)
        strategy_layout.addRow("删除模式", self.delete_mode_combo)

        self.rule_summary_label = QLabel("匹配规则：按 basename 匹配，忽略扩展名。")
        self.rule_summary_label.setWordWrap(True)
        strategy_layout.addRow("匹配规则", self.rule_summary_label)
        layout.addWidget(strategy_box)

        self.preview_button = QPushButton("生成预览")
        self.execute_button = QPushButton("执行清理")
        self.preview_button.clicked.connect(self._generate_preview)
        self.execute_button.clicked.connect(self._execute)

        action_row = QHBoxLayout()
        action_row.addWidget(self.preview_button)
        action_row.addWidget(self.execute_button)
        layout.addLayout(action_row)
        layout.addStretch()

        return box

    def _build_preview_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        preview_box = QGroupBox("预览结果")
        preview_layout = QVBoxLayout(preview_box)
        self.preview_summary_label = QLabel("生成预览后，将在这里展示保留和待处理列表。")
        self.preview_summary_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_summary_label)

        self.preview_table = QTableWidget(0, 5)
        self.preview_table.setHorizontalHeaderLabels(
            ["文件名", "完整路径", "匹配状态", "计划动作", "备注"]
        )
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        preview_layout.addWidget(self.preview_table)
        layout.addWidget(preview_box, 3)

        result_box = QGroupBox("状态与结果")
        result_layout = QVBoxLayout(result_box)
        self.status_label = QLabel("状态：等待输入")
        self.status_label.setWordWrap(True)
        result_layout.addWidget(self.status_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("统计摘要、失败原因和执行结果将在这里展示。")
        result_layout.addWidget(self.result_text)
        layout.addWidget(result_box, 1)

        return container

    def _choose_selected_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择成片目录")
        if not directory:
            return

        self.selected_dir = Path(directory)
        self.selected_dir_label.setText(str(self.selected_dir))
        self._mark_preview_stale("已更新成片目录，请重新生成预览。")

    def _choose_source_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择原片目录")
        if not directory:
            return

        self.source_dir = Path(directory)
        self.source_dir_label.setText(str(self.source_dir))
        self._mark_preview_stale("已更新原片目录，请重新生成预览。")

    def _clear_paths(self) -> None:
        self.selected_dir = None
        self.source_dir = None
        self.selected_dir_label.setText("未选择成片目录")
        self.source_dir_label.setText("未选择原片目录")
        self._clear_preview("状态：等待输入")

    def _preview_allowed(self) -> bool:
        return self.selected_dir is not None and self.source_dir is not None

    def _refresh_actions(self) -> None:
        self.preview_button.setEnabled(self._preview_allowed())
        self.execute_button.setEnabled(self.preview_ready)

    def _on_parameters_changed(self) -> None:
        if self.preview_ready:
            self._mark_preview_stale("策略已变化，请重新生成预览。")
        else:
            self._refresh_actions()

    def _mark_preview_stale(self, status: str) -> None:
        self.preview_ready = False
        self.status_label.setText(f"状态：{status}")
        self.result_text.clear()
        self.preview_summary_label.setText("当前预览已失效，请重新生成。")
        self._refresh_actions()

    def _clear_preview(self, status: str) -> None:
        self.preview_ready = False
        self.preview_table.setRowCount(0)
        self.preview_summary_label.setText("生成预览后，将在这里展示保留和待处理列表。")
        self.status_label.setText(status)
        self.result_text.clear()
        self._refresh_actions()

    def _generate_preview(self) -> None:
        if not self._preview_allowed():
            show_warning(self, "参数不完整", "请先选择成片目录和原片目录。")
            return

        rows = self._build_preview_rows()
        self.preview_table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for column_index, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.preview_table.setItem(row_index, column_index, item)

        self.preview_ready = True
        self.preview_summary_label.setText(
            f"已生成 {len(rows)} 条预览记录。当前为阶段 2 占位数据，用于验证保留/清理界面流转。"
        )
        self.status_label.setText("状态：预览已生成，等待确认执行")
        self.result_text.setPlainText(
            "预览完成\n"
            f"- 成片目录：{self.selected_dir}\n"
            f"- 原片目录：{self.source_dir}\n"
            f"- 删除模式：{self._delete_mode_label()}\n"
            "- 下一步可点击“执行清理”验证高风险操作的确认链路。"
        )
        self._refresh_actions()

    def _build_preview_rows(self) -> list[list[str]]:
        assert self.selected_dir is not None
        assert self.source_dir is not None

        keep_name = "IMG_0001.ARW"
        process_name = "IMG_9999.ARW"
        action = (
            "移动到回收站"
            if self.delete_mode_combo.currentData() == "trash"
            else "永久删除"
        )
        return [
            [
                keep_name,
                str(self.source_dir / keep_name),
                "已匹配",
                "保留",
                "与成片 IMG_0001.jpg basename 匹配",
            ],
            [
                process_name,
                str(self.source_dir / process_name),
                "未匹配",
                action,
                "阶段 2 占位预览",
            ],
        ]

    def _execute(self) -> None:
        if not self.preview_ready:
            show_warning(self, "尚未预览", "请先生成预览，再执行清理。")
            return

        summary = (
            f"成片目录：{self.selected_dir}\n"
            f"原片目录：{self.source_dir}\n"
            f"删除模式：{self._delete_mode_label()}\n"
            f"预览记录：{self.preview_table.rowCount()} 条"
        )
        if not confirm_cleanup(
            self,
            summary,
            permanent_delete=self.delete_mode_combo.currentData() == "permanent",
        ):
            self.status_label.setText("状态：用户取消执行")
            return

        self.status_label.setText("状态：已完成骨架阶段的执行演示")
        self.result_text.setPlainText(
            "执行完成（骨架演示）\n"
            f"- 总记录数：{self.preview_table.rowCount()}\n"
            "- 保留：1\n"
            "- 已处理：1\n"
            "- 失败：0\n"
            "- 当前阶段未移动或删除真实文件，仅验证了确认与结果展示链路。"
        )
        show_info(self, "执行完成", "阶段 2 的原片筛选页已完成确认与结果展示骨架。")

    def _delete_mode_label(self) -> str:
        return str(self.delete_mode_combo.currentText())
