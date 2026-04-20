from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QFileDialog,
    QDockWidget, QApplication, QLabel, QWidget, QVBoxLayout,
    QHBoxLayout, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QFormLayout, QMessageBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from frontend.app.app_controller import AppController
from frontend.canvas.scene import CircuitScene
from frontend.canvas.view import CircuitView
from frontend.panels.properties_panel import PropertiesPanel
from frontend.dialogs.settings_dialog import SettingsDialog
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.controller = AppController()
        self.setWindowTitle("Булевский редактор схем")
        self.resize(1200, 800)

        self.init_menu()
        self.init_toolbar()
        self.init_central()
        self.init_docks()

    def init_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")
        open_action = QAction("Открыть", self)
        save_action = QAction("Сохранить", self)
        exit_action = QAction("Выход", self)

        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("Правка")
        undo_action = QAction("Отмена", self)
        redo_action = QAction("Повтор", self)
        undo_action.triggered.connect(self.undo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)

        view_menu = menu_bar.addMenu("Вид")
        self.truth_table_action = QAction("Таблица истинности", self, checkable=True)
        self.simplify_action = QAction("Упрощение", self, checkable=True)
        self.polynomial_action = QAction("Полиномы", self, checkable=True)
        self.settings_action = QAction("Настройки", self)

        view_menu.addAction(self.truth_table_action)
        view_menu.addAction(self.simplify_action)
        view_menu.addAction(self.polynomial_action)
        view_menu.addSeparator()
        view_menu.addAction(self.settings_action)

        self.settings_action.triggered.connect(self.show_settings)

    def init_toolbar(self):
        toolbar = QToolBar("Элементы")
        self.addToolBar(toolbar)

        for gate in ["AND", "OR", "XOR", "EQUAL", "CONST_0", "CONST_1"]:
            action = QAction(gate, self)
            action.triggered.connect(lambda checked, g = gate: self.select_gate(g))
            toolbar.addAction(action)

        connect_action = QAction("Связь", self)
        connect_action.setCheckable(True)
        connect_action.triggered.connect(self.set_connect_mode)
        toolbar.addAction(connect_action)

        disconnect_action = QAction("Отключить", self)
        disconnect_action.setCheckable(True)
        disconnect_action.triggered.connect(self.set_disconnect_mode)
        toolbar.addAction(disconnect_action)

    def select_gate(self, gate_type):
        self.scene.set_selected_gate(gate_type)
        self.scene.mode = "add"
        print("Выбран узел:", gate_type)

    def set_connect_mode(self, checked=False):
        self.scene.mode = "connect"
        self.scene.connect_source_id = None
        print("Режим связи включен")

    def set_disconnect_mode(self, checked=False):
        self.scene.mode = "disconnect"
        self.scene.connect_source_id = None
        print("Режим отключения включен")


    def init_central(self):
        self.scene = CircuitScene(self.controller)
        self.view = CircuitView(self.scene)
        self.setCentralWidget(self.view)

    def init_docks(self):
        self.properties_dock = QDockWidget("Properties", self)
        self.properties_panel = PropertiesPanel()
        self.properties_panel.properties_changed.connect(self.on_properties_changed)
        self.properties_dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_dock)
        self.properties_dock.hide() 

        self.truth_table_dock = QDockWidget("Таблица истинности", self)

        dock_widget = QWidget()
        dock_layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Режим:"))
        self.truth_table_mode = QComboBox()
        self.truth_table_mode.addItems(["Схема", "По элементу"])
        controls_layout.addWidget(self.truth_table_mode)
        controls_layout.addStretch()
        self.refresh_truth_table_button = QPushButton("Обновить")
        controls_layout.addWidget(self.refresh_truth_table_button)
        dock_layout.addLayout(controls_layout)

        self.truth_table_info = QLabel("Выберите режим и узел")
        dock_layout.addWidget(self.truth_table_info)

        self.polynomial_label = QLabel("Полином: не выбран узел")
        self.polynomial_label.setWordWrap(True)
        self.polynomial_label.hide()
        dock_layout.addWidget(self.polynomial_label)

        self.truth_table_table = QTableWidget()
        dock_layout.addWidget(self.truth_table_table)

        self.fixed_inputs_label = QLabel("Фиксированные входы")
        dock_layout.addWidget(self.fixed_inputs_label)
        self.fixed_inputs_layout = QFormLayout()
        self.fixed_inputs_widget = QWidget()
        self.fixed_inputs_widget.setLayout(self.fixed_inputs_layout)
        dock_layout.addWidget(self.fixed_inputs_widget)

        self.evaluate_button = QPushButton("Оценить")
        self.simplify_button = QPushButton("Упростить")
        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.evaluate_button)
        actions_layout.addWidget(self.simplify_button)
        dock_layout.addLayout(actions_layout)

        self.eval_result_label = QLabel("")
        dock_layout.addWidget(self.eval_result_label)

        dock_widget.setLayout(dock_layout)
        self.truth_table_dock.setWidget(dock_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.truth_table_dock)
        self.truth_table_dock.hide()

        self.evaluate_button.clicked.connect(self.on_evaluate_clicked)
        self.simplify_button.clicked.connect(self.on_simplify_clicked)

        self.truth_table_action.toggled.connect(self.truth_table_dock.setVisible)
        self.truth_table_action.toggled.connect(lambda visible: self.update_truth_table_panel())
        self.polynomial_action.toggled.connect(self.on_polynomial_toggled)
        self.truth_table_mode.currentIndexChanged.connect(self.update_truth_table_panel)
        self.refresh_truth_table_button.clicked.connect(self.update_truth_table_panel)

        self.selected_node_id = None
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)

    def on_scene_selection_changed(self):
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 1:
            item = selected_items[0]
            if hasattr(item, "node_id"):
                self.selected_node_id = item.node_id
                node_data = self.controller.circuit.get_node(item.node_id)
                self.properties_panel.set_selected_node(node_data, self.controller.circuit)
                self.properties_dock.show()
            else:
                self.selected_node_id = None
                self.properties_panel.set_selected_node(None, self.controller.circuit)
        else:
            self.selected_node_id = None
            self.properties_panel.set_selected_node(None, self.controller.circuit)
        self.update_truth_table_panel()
        self.update_polynomial_display()

    def on_properties_changed(self, data):
        if data["action"] == "move_node":
            self.controller.move_node(data["node_id"], data["old_x"], data["old_y"], data["new_x"], data["new_y"])
            self.scene.sync_scene()

    def update_polynomial_display(self):
        if not self.polynomial_action.isChecked():
            self.polynomial_label.hide()
            return

        if self.selected_node_id is None:
            polynomials = self.controller.get_polynomials()
            text = "Полиномы схемы: "
            if isinstance(polynomials, str):
                text += polynomials
            elif isinstance(polynomials, dict):
                text += str(polynomials)
            elif polynomials is None:
                text += "не найдены"
            else:
                text += str(polynomials)
            self.polynomial_label.setText(text)
            self.polynomial_label.show()
            return

        poly = self.controller.get_polynomial_for_node(self.selected_node_id)
        if isinstance(poly, str):
            text = f"Полином узла #{self.selected_node_id}: {poly}"
        elif isinstance(poly, dict):
            text = f"Полином узла #{self.selected_node_id}: {poly}"
        elif poly is None:
            text = f"Полином узла #{self.selected_node_id}: не определен"
        else:
            text = f"Полином узла #{self.selected_node_id}: {poly}"
        self.polynomial_label.setText(text)
        self.polynomial_label.show()

    def on_polynomial_toggled(self, checked):
        self.polynomial_label.setVisible(checked)
        if checked:
            self.update_polynomial_display()

    def undo(self):
        if self.controller.undo():
            self.scene.sync_scene()

    def redo(self):
        if self.controller.redo():
            self.scene.sync_scene()

    def update_truth_table_panel(self):
        if not self.truth_table_action.isChecked():
            return

        mode = self.truth_table_mode.currentText()
        if mode == "Схема":
            table = self.controller.get_truth_table()
            if not table.get("inputs") and not table.get("outputs"):
                self.truth_table_info.setText("Схема не содержит входов и/или выходов")
                self.truth_table_table.clear()
                self.scene.clear_highlights()
                return
            self.truth_table_info.setText("Таблица истинности для всей схемы")
            headers = [f"IN_{nid}" for nid in table.get("inputs", [])] + [f"OUT_{nid}" for nid in table.get("outputs", [])]
            self._fill_truth_table(headers, table.get("rows", []))
            self.scene.clear_highlights()
        else:
            if self.selected_node_id is None:
                self.truth_table_info.setText("Режим по элементу: выберите узел на схеме")
                self.truth_table_table.clear()
                self.scene.clear_highlights()
                return
            table = self.controller.get_truth_table_for_node(self.selected_node_id)
            inputs = table.get("inputs", []) if isinstance(table, dict) else []
            node_id = table.get("node_id", self.selected_node_id) if isinstance(table, dict) else self.selected_node_id
            headers = [f"IN_{nid}" for nid in inputs] + [f"Node_{node_id}"]
            self.truth_table_info.setText(f"Таблица истинности узла #{self.selected_node_id}")
            self._fill_truth_table(headers, table.get("rows", []) if isinstance(table, dict) else [])
            affected = self.controller.get_affected_nodes(self.selected_node_id)
            self.scene.highlight_nodes(affected + [self.selected_node_id])
        self.update_polynomial_display()

    def _fill_truth_table(self, headers, rows):
        self.truth_table_table.clear()
        self.truth_table_table.setColumnCount(len(headers))
        self.truth_table_table.setRowCount(len(rows))
        self.truth_table_table.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(rows):
            for c, header in enumerate(headers):
                value = row.get(header, 0)
                item = QTableWidgetItem(str(value))
                self.truth_table_table.setItem(r, c, item)

    def update_fixed_inputs_panel(self):
        while self.fixed_inputs_layout.rowCount() > 0:
            self.fixed_inputs_layout.removeRow(0)
        self.input_value_controls = {}

        input_nodes = [n["id"] for n in self.controller.circuit.get_nodes() if n["type"].upper() == "IN"]
        if not input_nodes:
            return
        
        for nid in sorted(input_nodes):
            combo = QComboBox()
            combo.addItems(["0", "1"])
            self.input_value_controls[nid] = combo
            self.fixed_inputs_layout.addRow(QLabel(f"IN_{nid}"), combo)

    def get_fixed_input_values(self):
        return {nid: int(combo.currentText()) for nid, combo in self.input_value_controls.items()}

    def on_evaluate_clicked(self):
        self.update_fixed_inputs_panel()
        values = self.get_fixed_input_values()
        if not values:
            self.eval_result_label.setText("Нет входов для оценки")
            return
        
        try:
            report = self.controller.get_evaluation_report(values)
            if report and "row" in report:
                output_nodes = [n["id"] for n in self.controller.circuit.get_nodes() if n["type"].upper() == "OUT"]
                result_text = "Результаты: "
                for out_id in output_nodes:
                    val = report["row"].get(f"OUT_{out_id}", "?")
                    result_text += f"OUT_{out_id}={val} "
                self.eval_result_label.setText(result_text)
            else:
                self.eval_result_label.setText("Не удалось оценить схему")
        except Exception as e:
            self.eval_result_label.setText(f"Ошибка оценки: {str(e)}")

    def on_simplify_clicked(self):
        self.update_fixed_inputs_panel()
        values = self.get_fixed_input_values()
        if not values:
            self.eval_result_label.setText("Нет входов для упрощения")
            return
        
        try:
            self.controller.simplify_circuit(values)
            self.scene.sync_scene()
            self.update_truth_table_panel()
            self.eval_result_label.setText("Схема упрощена!")
        except Exception as e:
            self.eval_result_label.setText(f"Ошибка упрощения: {str(e)}")

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Открыть схему", "", "XML Files (*.xml)")
        if filepath:
            try:
                self.controller.load_circuit(filepath)
                self.scene.sync_scene()
                self.update_truth_table_panel()
                self.update_polynomial_display()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")

    def save_file(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить схему", "", "XML Files (*.xml)")
        if filepath:
            try:
                self.controller.save_circuit(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()