from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QFileDialog,
    QDockWidget, QApplication, QLabel, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from backend.application.app_controller import AppController
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
        delete_action = QAction("Удалить блок(и)", self)
        delete_action.setShortcut("Delete")
        undo_action.triggered.connect(self.undo)
        redo_action.triggered.connect(self.redo)
        delete_action.triggered.connect(self.delete_selected_nodes)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(delete_action)

        view_menu = menu_bar.addMenu("Вид")
        self.truth_table_action = QAction("Таблица истинности", self, checkable=True)
        self.settings_action = QAction("Настройки", self)

        view_menu.addAction(self.truth_table_action)
        view_menu.addSeparator()
        view_menu.addAction(self.settings_action)

        self.settings_action.triggered.connect(self.show_settings)

    def init_toolbar(self):
        toolbar = QToolBar("Элементы")
        self.addToolBar(toolbar)

        for gate in ["IN", "OUT", "AND", "OR", "XOR", "EQUAL"]:
            action = QAction(gate, self)
            action.triggered.connect(lambda checked, g = gate: self.select_gate(g))
            toolbar.addAction(action)

        toolbar.addSeparator()
        connect_action = QAction("Связь", self)
        connect_action.setCheckable(True)
        connect_action.triggered.connect(self.set_connect_mode)
        toolbar.addAction(connect_action)

        disconnect_action = QAction("Отключить", self)
        disconnect_action.setCheckable(True)
        disconnect_action.triggered.connect(self.set_disconnect_mode)
        toolbar.addAction(disconnect_action)

        delete_action = QAction("Удалить", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected_nodes)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()
        show_table_action = QAction("Показать таблицу", self)
        show_table_action.triggered.connect(self.show_truth_table)
        toolbar.addAction(show_table_action)

        help_action = QAction("Подсказка", self)
        help_action.triggered.connect(self.show_controls_help)
        toolbar.addAction(help_action)

    def select_gate(self, gate_type):
        self.scene.set_selected_gate(gate_type)
        self.scene.mode = "add"
        self.statusBar().showMessage(
            f"Выбран {gate_type}: кликните по пустому месту на доске для добавления",
            5000,
        )

    def set_connect_mode(self, checked=False):
        self.scene.set_connect_mode()
        self.statusBar().showMessage(
            "Режим связи: кликните по выходному пину, затем по входному",
            7000,
        )

    def set_disconnect_mode(self, checked=False):
        self.scene.set_disconnect_mode()
        self.statusBar().showMessage(
            "Режим отключения: кликните по линии связи или по паре пинов",
            7000,
        )

    def show_truth_table(self):
        self.truth_table_action.setChecked(True)
        self.truth_table_dock.show()
        self.update_truth_table_panel()

    def delete_selected_nodes(self):
        if self.scene.delete_selected_nodes():
            self.statusBar().showMessage("Выбранные блоки удалены", 3000)
            self.update_truth_table_panel()
        else:
            self.statusBar().showMessage("Нет выбранных блоков для удаления", 3000)

    def show_controls_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Подсказка по управлению")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet(
            "QLabel { min-width: 560px; font-size: 13px; }"
            "QPushButton { min-width: 120px; padding: 6px 14px; }"
        )
        msg.setText(
            "<h3>Быстрый старт</h3>"
            "<p><b>1.</b> Выберите элемент (<code>IN/OUT/AND/OR/XOR/EQUAL</code>) и кликните по доске.</p>"
            "<p><b>2.</b> Нажмите <b>Связь</b>: выходной пин -> входной пин.</p>"
            "<p><b>3.</b> Нажмите <b>Отключить</b> и кликните по линии для удаления.</p>"
            "<hr>"
            "<p><b>Клавиатура:</b></p>"
            "<p>Стрелки — движение по доске<br>"
            "<code>+</code>/<code>-</code> — масштаб<br>"
            "<code>Del</code>/<code>Backspace</code> — удалить выбранные блоки</p>"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()


    def init_central(self):
        self.scene = CircuitScene(self.controller)
        self.view = CircuitView(self.scene)
        self.setCentralWidget(self.view)
        self.view.setFocus()

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
        controls_layout.addWidget(QLabel("Таблица всей схемы"))
        controls_layout.addStretch()
        self.refresh_truth_table_button = QPushButton("Обновить")
        controls_layout.addWidget(self.refresh_truth_table_button)
        dock_layout.addLayout(controls_layout)

        self.truth_table_info = QLabel("Выберите режим и узел")
        dock_layout.addWidget(self.truth_table_info)

        self.truth_table_table = QTableWidget()
        dock_layout.addWidget(self.truth_table_table)

        dock_widget.setLayout(dock_layout)
        self.truth_table_dock.setWidget(dock_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.truth_table_dock)
        self.truth_table_action.setChecked(True)
        self.truth_table_dock.show()

        self.truth_table_action.toggled.connect(self.truth_table_dock.setVisible)
        self.truth_table_action.toggled.connect(lambda visible: self.update_truth_table_panel())
        self.refresh_truth_table_button.clicked.connect(self.update_truth_table_panel)

        self.selected_node_id = None
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)

    def on_scene_selection_changed(self):
        try:
            selected_items = self.scene.selectedItems()
        except RuntimeError:
            return
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

    def on_properties_changed(self, data):
        if data["action"] == "move_node":
            self.controller.move_node(data["node_id"], data["old_x"], data["old_y"], data["new_x"], data["new_y"])
            self.scene.sync_scene()

    def undo(self):
        if self.controller.undo():
            self.scene.sync_scene()

    def redo(self):
        if self.controller.redo():
            self.scene.sync_scene()

    def update_truth_table_panel(self):
        if not self.truth_table_action.isChecked():
            return

        table = self.controller.get_truth_table()
        if table.get("error"):
            self.truth_table_info.setText(f"Ошибка: {table['error']}")
            self.truth_table_table.clear()
            self.scene.clear_highlights()
            return
        if not table.get("inputs") and not table.get("outputs"):
            self.truth_table_info.setText("Схема не содержит входов и/или выходов")
            self.truth_table_table.clear()
            self.scene.clear_highlights()
            return
        self.truth_table_info.setText("Таблица истинности для всей схемы")
        headers = [f"IN_{nid}" for nid in table.get("inputs", [])] + [f"OUT_{nid}" for nid in table.get("outputs", [])]
        self._fill_truth_table(headers, table.get("rows", []))
        self.scene.clear_highlights()

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

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Открыть схему", "", "XML Files (*.xml)")
        if filepath:
            try:
                self.controller.load_circuit(filepath)
                self.scene.sync_scene()
                self.update_truth_table_panel()
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