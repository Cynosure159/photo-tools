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

from src.models.raw_cleanup import (
    RawCleanupExecutionResult,
    RawCleanupPreview,
    RawCleanupPreviewRecord,
)
from src.tasks.raw_cleanup import (
    build_raw_cleanup_request,
    execute_cleanup,
    generate_cleanup_preview,
)
from src.ui.dialogs import confirm_cleanup, show_info, show_warning


class RawCleanupPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.selected_dir: Path | None = None
        self.source_dir: Path | None = None
        self.preview: RawCleanupPreview | None = None

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
                "按“成片目录 -> 原片目录 -> 删除策略 -> 预览 -> 二次确认 -> 执行”"
                "的流程工作。"
            )
        )
        layout.addWidget(
            QLabel(
                "按文件名主体匹配，忽略扩展名。预览会展示保留与待处理文件，"
                "执行时按所选策略移动到回收站或永久删除。"
            )
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

        self.rule_summary_label = QLabel("匹配规则：按文件名主体匹配，忽略扩展名。")
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
        self.preview_summary_label = QLabel(
            "生成预览后，将在这里展示保留和待处理列表。"
        )
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
        self.execute_button.setEnabled(self._has_executable_preview())

    def _on_parameters_changed(self) -> None:
        if self.preview is not None:
            self._mark_preview_stale("策略已变化，请重新生成预览。")
        else:
            self._refresh_actions()

    def _mark_preview_stale(self, status: str) -> None:
        self._reset_preview_state(
            summary="当前预览已失效，请重新生成。",
            status=f"状态：{status}",
        )

    def _clear_preview(self, status: str) -> None:
        self._reset_preview_state(
            summary="生成预览后，将在这里展示保留和待处理列表。",
            status=status,
        )

    def _generate_preview(self) -> None:
        if not self._preview_allowed():
            show_warning(self, "参数不完整", "请先选择成片目录和原片目录。")
            return

        preview = generate_cleanup_preview(self._build_request())
        self.preview = preview
        self._populate_preview_table(preview.records)
        self.preview_summary_label.setText(self._preview_summary_text(preview))
        self.status_label.setText(self._preview_status(preview))
        self.result_text.setPlainText(self._preview_result_text(preview))
        self._refresh_actions()

    def _execute(self) -> None:
        if self.preview is None:
            show_warning(self, "尚未预览", "请先生成预览，再执行清理。")
            return

        summary = (
            f"成片目录：{self.selected_dir}\n"
            f"原片目录：{self.source_dir}\n"
            f"删除模式：{self._delete_mode_label()}\n"
            f"预览记录：{len(self.preview.records)} 条\n"
            f"待处理：{self.preview.process_count} 条"
        )
        if not confirm_cleanup(
            self,
            summary,
            permanent_delete=self.delete_mode_combo.currentData() == "permanent",
        ):
            self.status_label.setText("状态：用户取消执行")
            return

        result = execute_cleanup(self._build_request(), self.preview)
        self.status_label.setText("状态：执行完成")
        self.result_text.setPlainText(self._execution_result_text(result))
        show_info(self, "执行完成", "原片清理已完成，请查看结果摘要。")
        self.preview = None
        self._refresh_actions()

    def _delete_mode_label(self) -> str:
        return str(self.delete_mode_combo.currentText())

    def _build_request(self):
        assert self.selected_dir is not None
        assert self.source_dir is not None
        return build_raw_cleanup_request(
            selected_dir=self.selected_dir,
            source_dir=self.source_dir,
            delete_mode=str(self.delete_mode_combo.currentData()),
        )

    def _reset_preview_state(self, *, summary: str, status: str) -> None:
        self.preview = None
        self.preview_table.setRowCount(0)
        self.preview_summary_label.setText(summary)
        self.status_label.setText(status)
        self.result_text.clear()
        self._refresh_actions()

    def _has_executable_preview(self) -> bool:
        return self.preview is not None and self.preview.process_count > 0

    def _preview_row_values(self, row: RawCleanupPreviewRecord) -> list[str]:
        return [
            row.name,
            str(row.path),
            "已匹配" if row.matched else "未匹配",
            row.planned_action,
            row.message,
        ]

    def _populate_preview_table(
        self, records: tuple[RawCleanupPreviewRecord, ...]
    ) -> None:
        self.preview_table.setRowCount(len(records))
        for row_index, row in enumerate(records):
            for column_index, value in enumerate(self._preview_row_values(row)):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.preview_table.setItem(row_index, column_index, item)

    def _preview_summary_text(self, preview: RawCleanupPreview) -> str:
        return (
            "预览已生成："
            f" 成片 {preview.selected_count} 个，原片 {preview.source_count} 个，"
            f"保留 {preview.keep_count} 个，待处理 {preview.process_count} 个。"
        )

    def _preview_status(self, preview: RawCleanupPreview) -> str:
        if preview.selected_count == 0:
            return "状态：成片目录中未识别到可匹配文件"
        if preview.source_count == 0:
            return "状态：原片目录中未识别到可处理文件"
        if preview.process_count == 0:
            return "状态：预览已生成，无需清理"
        return "状态：预览已生成，等待确认执行"

    def _preview_result_text(self, preview: RawCleanupPreview) -> str:
        lines = [
            "预览完成",
            f"- 成片目录：{self.selected_dir}",
            f"- 原片目录：{self.source_dir}",
            f"- 删除模式：{self._delete_mode_label()}",
            f"- 成片识别数量：{preview.selected_count}",
            f"- 原片扫描数量：{preview.source_count}",
            f"- 将保留：{preview.keep_count}",
            f"- 将处理：{preview.process_count}",
        ]
        lines.append(self._preview_next_step_message(preview))
        return "\n".join(lines)

    def _preview_next_step_message(self, preview: RawCleanupPreview) -> str:
        if preview.selected_count == 0:
            return "- 当前成片目录未找到可识别照片，原片不会命中任何文件名主体。"
        if preview.process_count == 0:
            return "- 当前预览下没有未匹配文件，不需要执行清理。"
        return "- 可继续点击“执行清理”进入二次确认。"

    def _execution_result_text(self, result: RawCleanupExecutionResult) -> str:
        lines = [
            "执行完成",
            f"- 总记录数：{result.total}",
            f"- 保留：{result.kept}",
            f"- 实际处理：{result.processed}",
            f"- 成功：{result.succeeded}",
            f"- 失败：{result.failed}",
        ]
        failed_records = [
            record for record in result.records if record.status == "失败"
        ]
        if failed_records:
            lines.append("- 失败项：")
            lines.extend(
                f"  - {record.path.name}：{record.message}" for record in failed_records
            )
        return "\n".join(lines)
