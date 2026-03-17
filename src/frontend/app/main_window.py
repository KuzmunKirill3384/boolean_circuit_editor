# app/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QAction, QToolBar, QFileDialog,
    QDockWidget, QApplication, QLabel, QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
from app.app_controller import AppController
from canvas.scene import CircuitScene
from canvas.view import CircuitView
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
        undo_action.triggered.connect(self.controller.undo)
        redo_action.triggered.connect(self.controller.redo)
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

    def init_toolbar(self):
        toolbar = QToolBar("Элементы")
        self.addToolBar(toolbar)

        for gate in ["AND", "OR", "XOR", "EQUAL"]:
            action = QAction(gate, self)
            action.triggered.connect(lambda checked, g=gate: self.select_gate(g))
            toolbar.addAction(action)

    def select_gate(self, gate_type):
        print("Выбран узел:", gate_type)


    def init_central(self):
        self.scene = CircuitScene(self.controller)
        self.view = CircuitView(self.scene)
        self.setCentralWidget(self.view)

    def init_docks(self):
        self.truth_table_dock = QDockWidget("Таблица истинности", self)
        label = QLabel("Здесь будет таблица истинности")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dock_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(label)
        dock_widget.setLayout(layout)
        self.truth_table_dock.setWidget(dock_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.truth_table_dock)
        self.truth_table_dock.hide()

        self.truth_table_action.toggled.connect(self.truth_table_dock.setVisible)

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Открыть схему", "", "XML Files (*.xml)")
        if filepath:
            self.controller.load_circuit(filepath)
            self.scene.sync_scene()

    def save_file(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить схему", "", "XML Files (*.xml)")
        if filepath:
            self.controller.save_circuit(filepath)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())