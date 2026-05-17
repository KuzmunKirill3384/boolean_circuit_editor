from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QTextEdit, QMessageBox, QDialogButtonBox, QPushButton, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class PolynomialDialog(QDialog):
    """Диалоговое окно для отображения полиномиального представления логических элементов схемы."""
    def __init__(self, parent=None, controller=None, circuit=None):
        super().__init__(parent)
        self.controller = controller
        self.circuit = circuit
        self.setWindowTitle("Полиномиальное представление")
        self.resize(800, 600)

        self.polynomials = {} 
        self.selected_node_id = None
        self.current_polynomial = ""
        
        self.init_ui()
        self.load_polynomials()
    
    def init_ui(self):
        """Инициализация интерфейса диалогового окна с деревом элементов и полем для полинома."""
        layout = QVBoxLayout()
        
        title_label = QLabel("Полиномиальное представление логических элементов")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title_label)

        info_label = QLabel(
            "Обозначения: * = AND, + = OR, ^ = XOR, ~^ = EQUAL, x№ = вход №"
        )
        info_label.setStyleSheet("color: gray; font-size: 10px; margin-bottom: 10px;")
        layout.addWidget(info_label)

        content_layout = QHBoxLayout()


        left_layout = QVBoxLayout()
        left_group = QGroupBox("Элементы схемы")
 
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Элемент", "Тип"])
        self.tree_widget.setMaximumWidth(300)
        self.tree_widget.itemSelectionChanged.connect(self.on_node_selected)
        
        left_layout.addWidget(self.tree_widget)
        left_group.setLayout(left_layout)
        content_layout.addWidget(left_group)

        right_layout = QVBoxLayout()
        right_group = QGroupBox("Полиномиальное представление")
        
        # Метка с информацией о выбранном элементе
        self.details_label = QLabel("Выберите элемент для просмотра его полинома")
        self.details_label.setStyleSheet("color: gray;")
        self.details_label.setWordWrap(True)
        
        # Поле для отображения полинома (только для чтения)
        self.polynomial_text = QTextEdit()
        self.polynomial_text.setReadOnly(True)
        self.polynomial_text.setFont(QFont("Courier", 10))
        
        # Кнопки копирования полиномов
        copy_buttons_layout = QHBoxLayout()
        self.copy_current_button = QPushButton("Копировать текущий")
        self.copy_current_button.clicked.connect(self.copy_current_polynomial)
        self.copy_current_button.setEnabled(False)
        
        self.copy_all_button = QPushButton("Копировать все")
        self.copy_all_button.clicked.connect(self.copy_all_polynomials)
        self.copy_all_button.setEnabled(False)
        
        copy_buttons_layout.addWidget(self.copy_current_button)
        copy_buttons_layout.addWidget(self.copy_all_button)
        
        right_layout.addWidget(self.details_label)
        right_layout.addWidget(self.polynomial_text)
        right_layout.addLayout(copy_buttons_layout)
        right_group.setLayout(right_layout)
        content_layout.addWidget(right_group)
        
        layout.addLayout(content_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    # Загрузка полиномов из контроллера с проверкой ошибок
    def load_polynomials(self):

        if not self.controller or not self.circuit:
            self._show_error("Контроллер или схема не инициализированы")
            return
        
        try:

            valid, reason = self.circuit.validate_structure()
            if not valid:
                self._show_error(f"Невалидная схема: {reason}")
                return

            nodes = self.circuit.get_nodes()
            if not nodes:
                self._show_error("Схема пуста: нет элементов")
                return

            self.polynomials = self.controller.get_polynomials()
            self._populate_tree()
            self.copy_all_button.setEnabled(bool(self.polynomials))
            
        except ValueError as e:
            self._show_error(f"Ошибка валидации: {e}")
        except Exception as e:
            self._show_error(f"Ошибка при загрузке полиномов: {e}")
    
    # Отображение сообщения об ошибке в окне диалога
    def _show_error(self, message: str):

        self.tree_widget.clear()
        error_item = QTreeWidgetItem(["Ошибка", ""])
        error_item.setStyleSheet("color: red;")
        error_msg = QTreeWidgetItem([message, ""])
        error_msg.setStyleSheet("color: red; font-style: italic;")
        error_item.addChild(error_msg)
        self.tree_widget.addTopLevelItem(error_item)
        self.tree_widget.expandAll()
        
        self.details_label.setText("❌ " + message)
        self.details_label.setStyleSheet("color: red; font-weight: bold;")
        self.polynomial_text.clear()
        self.copy_current_button.setEnabled(False)
        self.copy_all_button.setEnabled(False)
    
    # Заполнение дерева элементами, сгруппированными по типам
    def _populate_tree(self):

        self.tree_widget.clear()
        
        nodes_by_type = {}
        for node in self.circuit.get_nodes():
            node_type = node["type"]
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)

        type_order = ["IN", "AND", "OR", "XOR", "EQUAL", "CONST_0", "CONST_1", "OUT"]
        
        for node_type in type_order:
            if node_type in nodes_by_type:
                type_item = QTreeWidgetItem([node_type, ""])
                type_item.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
                self.tree_widget.addTopLevelItem(type_item)

                for node in nodes_by_type[node_type]:
                    node_id = node["id"]
                    node_label = f"#{node_id}"
                    node_item = QTreeWidgetItem([node_label, node_type])
                    node_item.setData(0, Qt.ItemDataRole.UserRole, node_id)
                    type_item.addChild(node_item)

        self.tree_widget.expandAll()
    
    # Обработчик выбора элемента в дереве - отображает его полином
    def on_node_selected(self):

        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        
        if node_id is None:
            self.details_label.setText("Выберите конкретный элемент")
            self.details_label.setStyleSheet("color: gray;")
            self.polynomial_text.clear()
            self.selected_node_id = None
            self.current_polynomial = ""
            self.copy_current_button.setEnabled(False)
            return
        
        self.selected_node_id = node_id
        node = self.circuit.get_node(node_id)
        polynomial = self.polynomials.get(node_id, "?")
        
        if not node:
            return

        details_text = (
            f"Элемент: #{node_id}\n"
            f"Тип: {node['type']}\n"
            f"Позиция: ({node['x']:.0f}, {node['y']:.0f})"
        )
        self.details_label.setText(details_text)
        self.details_label.setStyleSheet("")

        self.current_polynomial = f"f_{node_id} = {polynomial}"
        self.polynomial_text.setText(self.current_polynomial)
        self.copy_current_button.setEnabled(True)
    
    # Копирование текущего полинома в буфер обмена
    def copy_current_polynomial(self):

        if not self.current_polynomial:
            QMessageBox.warning(self, "Предупреждение", "Выберите элемент для копирования")
            return
        
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_polynomial)
            QMessageBox.information(self, "Успешно", "Полином скопирован в буфер обмена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать: {e}")
    
    # Копирование всех полиномов схемы в буфер обмена
    def copy_all_polynomials(self):

        all_text = self._get_all_polynomials_text()
        
        if not all_text:
            QMessageBox.warning(self, "Предупреждение", "Нет полиномов для копирования")
            return
        
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(all_text)
            QMessageBox.information(self, "Успешно", "Все полиномы скопированы в буфер обмена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать: {e}")
    
    # Форматирование всех полиномов для вывода
    def _get_all_polynomials_text(self) -> str:

        if not self.polynomials:
            return ""
        
        output = []
        for node_id in sorted(self.polynomials.keys()):
            node = self.circuit.get_node(node_id)
            if node:
                node_type = node["type"]
                poly = self.polynomials[node_id]
                output.append(f"f_{node_id} ({node_type}): {poly}")
        
        return "\n".join(output)
