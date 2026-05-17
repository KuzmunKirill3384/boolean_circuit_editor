from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QFormLayout, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QDialogButtonBox, QSpinBox, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
import copy



class SimplificationDialog(QDialog):
    """Диалоговое окно для упрощения схемы на основе известных значений входов. """
    def __init__(self, parent=None, controller=None, circuit=None):
        super().__init__(parent)
        self.controller = controller
        self.circuit = circuit
        self.setWindowTitle("Упрощение схемы")
        self.resize(700, 800)

        # Отбор сносителяя всех элементов входа из схемы
        self.input_nodes = []
        if circuit:
            for node in circuit.get_nodes():
                if node["type"] == "IN":
                    self.input_nodes.append(node)
            self.input_nodes.sort(key=lambda n: n["id"])
        
        
        self.input_values = {}

        self.removable_labels = {}

        self.value_combos = {}

        self.removable_info = {}
        
        self.total_nodes_label = None
        self.removable_nodes_label = None
        
        self.init_ui()
        self.update_removable_counts()
    
    def init_ui(self):
        layout = QVBoxLayout()
        

        title_label = QLabel("Укажите известные значения входов для упрощения схемы")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)

        input_group = QGroupBox("Значения входов и удаляемые элементы")
        input_layout = QFormLayout()
        
        if not self.input_nodes:
            no_input_label = QLabel("В схеме нет входов")
            input_layout.addRow(no_input_label)
        else:
            for node in self.input_nodes:
                node_id = node["id"]

                combo = QComboBox()
                combo.addItems(["Не установлено", "0", "1"])
                combo.setCurrentIndex(0)
                combo.currentIndexChanged.connect(self.on_input_value_changed)
                
                self.value_combos[node_id] = combo
                self.input_values[node_id] = None

                removable_label = QLabel("—")
                removable_label.setStyleSheet("color: green;")
                self.removable_labels[node_id] = removable_label

                h_layout = QHBoxLayout()
                h_layout.addWidget(combo)
                h_layout.addWidget(QLabel("(удалится:"))
                h_layout.addWidget(removable_label)
                h_layout.addWidget(QLabel("элементов)"))
                h_layout.addStretch()
                
                label_text = f"Вход {node_id}:"
                input_layout.addRow(label_text, h_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        summary_group = QGroupBox("Итого при упрощении")
        summary_layout = QVBoxLayout()
        
        summary_row1 = QHBoxLayout()
        summary_row1.addWidget(QLabel("Всего элементов в схеме:"))
        self.total_nodes_label = QLabel("0")
        self.total_nodes_label.setStyleSheet("font-weight: bold;")
        summary_row1.addWidget(self.total_nodes_label)
        summary_row1.addStretch()
        summary_layout.addLayout(summary_row1)
        
        summary_row2 = QHBoxLayout()
        summary_row2.addWidget(QLabel("Будет удалено при упрощении:"))
        self.removable_nodes_label = QLabel("0")
        self.removable_nodes_label.setStyleSheet("color: green; font-weight: bold;")
        summary_row2.addWidget(self.removable_nodes_label)
        summary_row2.addStretch()
        summary_layout.addLayout(summary_row2)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        info_text = QLabel(
            "Выберите значения для входов, которые вы считаете известными.\n"
            "Для каждого входа показано, сколько элементов можно удалить.\n"
            "Нажмите 'Применить' для упрощения схемы."
        )
        info_text.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_text)
        
        layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.apply_simplification)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    # Обработчик изменения значений входов - наполняет данные и поновляет счетЧики
    def on_input_value_changed(self):

        for node_id, combo in self.value_combos.items():
            index = combo.currentIndex()
            if index == 0:
                self.input_values[node_id] = None
            elif index == 1: 
                self.input_values[node_id] = 0
            else:  
                self.input_values[node_id] = 1

        
        self.update_removable_counts()
    
    # Обновление счетчиков удаляемых элементов как отображение в метках
    def update_removable_counts(self):
        if not self.controller or not self.circuit:
            return
        
        try:
            from backend.logic.truth_table import simplify
            
            # Получаем название элементов которые могут быть удалены для каждого входа
            removable_info = self.controller.get_removable_count_per_input()
            self.removable_info = removable_info

            # Получаем текущие выбранные значения (только не None)
            current_values = {k: v for k, v in self.input_values.items() if v is not None}
 
            total_removable = 0
            
            for node_id in sorted(self.removable_labels.keys()):
                if node_id in removable_info:
                    info = removable_info[node_id]
                    if node_id in current_values:
                        # Вход настроен, показываем отдельные количества
                        val = current_values[node_id]
                        if val == 0:
                            removable_count = info.get("if_0", 0)
                        else:
                            removable_count = info.get("if_1", 0)
                        self.removable_labels[node_id].setText(str(removable_count))
                        total_removable += removable_count
                    else:
                        if_0 = info.get("if_0", 0)
                        if_1 = info.get("if_1", 0)
                        # Отображаем в виде: "0→X, 1→Y"
                        self.removable_labels[node_id].setText(f"0→{if_0}, 1→{if_1}")

            total_nodes = len(self.circuit.get_nodes())
            
            if current_values:
                try:
                   
                    circuit_copy = copy.deepcopy(self.circuit)
                    simplified = simplify(circuit_copy, current_values)
                    total_removable = max(0, total_nodes - len(simplified.get_nodes()))
                except Exception as e:
                    total_removable = 0

            self.total_nodes_label.setText(str(total_nodes))
            self.removable_nodes_label.setText(str(total_removable))
            
        except Exception as e:

            pass
    
    
    def apply_simplification(self):
        """Применяет упрощение схемы на основе выбранных значений входов и закрывает диалог."""
        current_values = {k: v for k, v in self.input_values.items() if v is not None}
        
        if not current_values:
            QMessageBox.warning(self, "Предупреждение", "Остановите хотя бы одно значение входа")
            return
        
        try:
            # Применяем упрощение через контроллер
            if self.controller:

                self.controller.simplify_circuit(current_values)
                QMessageBox.information(self, "Успех", "Схема упрощена успешно")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось упростить схему: {str(e)}")

