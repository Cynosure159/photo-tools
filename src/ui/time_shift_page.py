from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.dialogs import confirm_time_shift, show_info, show_warning


class TimeShiftPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.selected_files: list[Path] = []
        self.selected_directory: Path | None = None
        self.preview_ready = False

        root_layout = QVBoxLayout(self)
        root_layout.addWidget(self._build_intro())

        content_layout = QHBoxLayout()
        content_layout.addWidget(self._build_controls(), 1)
        content_layout.addWidget(self._build_preview_area(), 2)
        root_layout.addLayout(content_layout)

        self._refresh_actions()

    def _build_intro(self) -> QGroupBox:
        box = QGroupBox("批量修改照片时间")
        layout = QVBoxLayout(box)
        layout.addWidget(
            QLabel(
                "按“选择输入 -> 配置偏移 -> 生成预览 -> 二次确认 -> 执行”的流程工作。"
            )
        )
        layout.addWidget(
            QLabel("阶段 2 为 GUI 骨架，当前预览和结果仅用于承载交互与状态。")
        )
        return box

    def _build_controls(self) -> QGroupBox:
        box = QGroupBox("输入与配置")
        layout = QVBoxLayout(box)

        input_box = QGroupBox("选择输入")
        input_layout = QVBoxLayout(input_box)

        button_row = QHBoxLayout()
        self.select_files_button = QPushButton("选择文件")
        self.select_folder_button = QPushButton("选择文件夹")
        self.clear_input_button = QPushButton("清空输入")
        self.select_files_button.clicked.connect(self._choose_files)
        self.select_folder_button.clicked.connect(self._choose_directory)
        self.clear_input_button.clicked.connect(self._clear_input)
        button_row.addWidget(self.select_files_button)
        button_row.addWidget(self.select_folder_button)
        button_row.addWidget(self.clear_input_button)
        input_layout.addLayout(button_row)

        self.input_summary_label = QLabel("尚未选择文件或文件夹。")
        self.input_summary_label.setWordWrap(True)
        input_layout.addWidget(self.input_summary_label)

        self.selected_list = QListWidget()
        self.selected_list.setMinimumHeight(140)
        input_layout.addWidget(self.selected_list)
        layout.addWidget(input_box)

        config_box = QGroupBox("偏移量与字段")
        config_layout = QFormLayout(config_box)

        offset_grid = QGridLayout()
        self.days_spin = self._create_offset_spinbox("天")
        self.hours_spin = self._create_offset_spinbox("小时")
        self.minutes_spin = self._create_offset_spinbox("分钟")
        self.seconds_spin = self._create_offset_spinbox("秒")
        offset_grid.addWidget(QLabel("天"), 0, 0)
        offset_grid.addWidget(self.days_spin, 0, 1)
        offset_grid.addWidget(QLabel("小时"), 0, 2)
        offset_grid.addWidget(self.hours_spin, 0, 3)
        offset_grid.addWidget(QLabel("分钟"), 1, 0)
        offset_grid.addWidget(self.minutes_spin, 1, 1)
        offset_grid.addWidget(QLabel("秒"), 1, 2)
        offset_grid.addWidget(self.seconds_spin, 1, 3)
        config_layout.addRow("时间偏移", offset_grid)

        field_row = QHBoxLayout()
        self.update_created_checkbox = QCheckBox("创建时间")
        self.update_modified_checkbox = QCheckBox("修改时间")
        self.update_taken_checkbox = QCheckBox("拍摄时间")
        self.update_modified_checkbox.setChecked(True)
        for checkbox in (
            self.update_created_checkbox,
            self.update_modified_checkbox,
            self.update_taken_checkbox,
        ):
            checkbox.stateChanged.connect(self._on_parameters_changed)
            field_row.addWidget(checkbox)
        field_row.addStretch()
        config_layout.addRow("修改字段", field_row)

        for spinbox in (
            self.days_spin,
            self.hours_spin,
            self.minutes_spin,
            self.seconds_spin,
        ):
            spinbox.valueChanged.connect(self._on_parameters_changed)

        self.preview_button = QPushButton("生成预览")
        self.execute_button = QPushButton("执行修改")
        self.preview_button.clicked.connect(self._generate_preview)
        self.execute_button.clicked.connect(self._execute)

        action_row = QHBoxLayout()
        action_row.addWidget(self.preview_button)
        action_row.addWidget(self.execute_button)
        layout.addWidget(config_box)
        layout.addLayout(action_row)
        layout.addStretch()
        return box

    def _build_preview_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        preview_box = QGroupBox("预览结果")
        preview_layout = QVBoxLayout(preview_box)
        self.preview_summary_label = QLabel("生成预览后，将在这里展示逐文件对比。")
        self.preview_summary_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_summary_label)

        self.preview_table = QTableWidget(0, 10)
        self.preview_table.setHorizontalHeaderLabels(
            [
                "文件名",
                "路径",
                "原创建时间",
                "新创建时间",
                "原修改时间",
                "新修改时间",
                "原拍摄时间",
                "新拍摄时间",
                "状态",
                "备注",
            ]
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
        self.result_text.setPlaceholderText("执行摘要、失败原因和后续结果将在这里展示。")
        result_layout.addWidget(self.result_text)
        layout.addWidget(result_box, 1)

        return container

    def _create_offset_spinbox(self, suffix: str) -> QSpinBox:
        spinbox = QSpinBox()
        spinbox.setRange(-9999, 9999)
        spinbox.setSuffix(f" {suffix}")
        return spinbox

    def _choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择待处理照片",
            "",
            "Images (*.jpg *.jpeg *.png *.heic *.tif *.tiff *.arw *.cr2 *.nef *.dng);;All Files (*)",
        )
        if not files:
            return

        self.selected_files = [Path(file) for file in files]
        self.selected_directory = None
        self._fill_input_list()
        self._mark_preview_stale("已选择文件，等待生成预览。")

    def _choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择待扫描文件夹")
        if not directory:
            return

        self.selected_directory = Path(directory)
        self.selected_files = []
        self._fill_input_list()
        self._mark_preview_stale("已选择文件夹，等待生成预览。")

    def _clear_input(self) -> None:
        self.selected_files = []
        self.selected_directory = None
        self.selected_list.clear()
        self.input_summary_label.setText("尚未选择文件或文件夹。")
        self._clear_preview("状态：等待输入")

    def _fill_input_list(self) -> None:
        self.selected_list.clear()

        if self.selected_files:
            for file_path in self.selected_files:
                QListWidgetItem(str(file_path), self.selected_list)
            self.input_summary_label.setText(f"已选择 {len(self.selected_files)} 个文件。")
            return

        if self.selected_directory is not None:
            QListWidgetItem(str(self.selected_directory), self.selected_list)
            self.input_summary_label.setText(
                f"已选择文件夹：{self.selected_directory}"
            )

    def _has_input(self) -> bool:
        return bool(self.selected_files) or self.selected_directory is not None

    def _has_selected_fields(self) -> bool:
        return any(
            checkbox.isChecked()
            for checkbox in (
                self.update_created_checkbox,
                self.update_modified_checkbox,
                self.update_taken_checkbox,
            )
        )

    def _has_offset(self) -> bool:
        return any(
            spinbox.value() != 0
            for spinbox in (
                self.days_spin,
                self.hours_spin,
                self.minutes_spin,
                self.seconds_spin,
            )
        )

    def _preview_allowed(self) -> bool:
        return self._has_input() and self._has_selected_fields() and self._has_offset()

    def _refresh_actions(self) -> None:
        self.preview_button.setEnabled(self._preview_allowed())
        self.execute_button.setEnabled(self.preview_ready)

    def _on_parameters_changed(self) -> None:
        if self.preview_ready:
            self._mark_preview_stale("参数已变化，请重新生成预览。")
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
        self.preview_summary_label.setText("生成预览后，将在这里展示逐文件对比。")
        self.status_label.setText(status)
        self.result_text.clear()
        self._refresh_actions()

    def _generate_preview(self) -> None:
        if not self._preview_allowed():
            show_warning(self, "参数不完整", "请先选择输入、勾选至少一个字段，并设置非零偏移量。")
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
            f"已生成 {len(rows)} 条预览记录。当前为阶段 2 占位数据，用于验证界面流转。"
        )
        self.status_label.setText("状态：预览已生成，等待确认执行")
        self.result_text.setPlainText(
            "预览完成\n"
            f"- 输入来源：{self._input_description()}\n"
            f"- 偏移量：{self._offset_description()}\n"
            f"- 修改字段：{self._field_description()}\n"
            "- 下一步可点击“执行修改”验证确认链路。"
        )
        self._refresh_actions()

    def _build_preview_rows(self) -> list[list[str]]:
        targets: list[tuple[str, str]]

        if self.selected_files:
            targets = [(path.name, str(path)) for path in self.selected_files]
        else:
            assert self.selected_directory is not None
            targets = [
                (
                    "目录扫描占位.jpg",
                    str(self.selected_directory / "目录扫描占位.jpg"),
                )
            ]

        rows: list[list[str]] = []
        for index, (name, path) in enumerate(targets, start=1):
            created_before = f"2024-05-{index:02d} 10:00:00"
            modified_before = f"2024-05-{index:02d} 10:05:00"
            taken_before = "2024-05-01 09:30:00" if self.update_taken_checkbox.isChecked() else "不修改"
            rows.append(
                [
                    name,
                    path,
                    created_before,
                    self._after_value(created_before, self.update_created_checkbox.isChecked()),
                    modified_before,
                    self._after_value(modified_before, self.update_modified_checkbox.isChecked()),
                    taken_before if self.update_taken_checkbox.isChecked() else "不修改",
                    self._after_value("2024-05-01 09:30:00", self.update_taken_checkbox.isChecked()),
                    "待执行",
                    "阶段 2 占位预览",
                ]
            )

        return rows

    def _after_value(self, before: str, enabled: bool) -> str:
        return f"{before} {self._offset_description()}" if enabled else "不修改"

    def _execute(self) -> None:
        if not self.preview_ready:
            show_warning(self, "尚未预览", "请先生成预览，再执行修改。")
            return

        summary = (
            f"输入来源：{self._input_description()}\n"
            f"偏移量：{self._offset_description()}\n"
            f"修改字段：{self._field_description()}\n"
            f"预览记录：{self.preview_table.rowCount()} 条"
        )
        if not confirm_time_shift(self, summary):
            self.status_label.setText("状态：用户取消执行")
            return

        self.status_label.setText("状态：已完成骨架阶段的执行演示")
        self.result_text.setPlainText(
            "执行完成（骨架演示）\n"
            f"- 总记录数：{self.preview_table.rowCount()}\n"
            f"- 成功：{self.preview_table.rowCount()}\n"
            "- 失败：0\n"
            "- 跳过：0\n"
            "- 当前阶段未写入真实文件，仅验证了确认与结果展示链路。"
        )
        show_info(self, "执行完成", "阶段 2 的时间修改页已完成确认与结果展示骨架。")

    def _input_description(self) -> str:
        if self.selected_files:
            return f"{len(self.selected_files)} 个文件"
        if self.selected_directory is not None:
            return f"文件夹 {self.selected_directory}"
        return "未选择"

    def _offset_description(self) -> str:
        parts: list[str] = []
        mapping = [
            (self.days_spin.value(), "天"),
            (self.hours_spin.value(), "小时"),
            (self.minutes_spin.value(), "分钟"),
            (self.seconds_spin.value(), "秒"),
        ]
        for value, unit in mapping:
            if value:
                parts.append(f"{value:+d} {unit}")
        return " ".join(parts) if parts else "0"

    def _field_description(self) -> str:
        labels: list[str] = []
        if self.update_created_checkbox.isChecked():
            labels.append("创建时间")
        if self.update_modified_checkbox.isChecked():
            labels.append("修改时间")
        if self.update_taken_checkbox.isChecked():
            labels.append("拍摄时间")
        return "、".join(labels) if labels else "未选择"
