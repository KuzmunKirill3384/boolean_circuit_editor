from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog,
    QFontDialog, QSpinBox, QGroupBox, QFormLayout, QDialogButtonBox
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from frontend.common.settings import SettingsManager

# Диалоговое окно для управления настройками внешнего вида приложения (цвета, шрифты, размеры)
class SettingsDialog(QDialog):
    # Инициализация диалога настроек с загрузкой текущих значений из SettingsManager
    def __init__(self, parent = None):
        super().__init__(parent)
        self.settings_manager = SettingsManager()
        self.setWindowTitle("Настройки")
        self.resize(400, 600)

        # Список всех типов элементов для которых настраиваются цвета
        self.node_types = ["AND", "OR", "XOR", "EQUAL", "IN", "OUT", "CONST_0", "CONST_1"]

        # Загрузка текущих настроек внешнего вида
        self.current_node_colors = {nt: self.settings_manager.get_node_color(nt) for nt in self.node_types}
        self.current_line_color = self.settings_manager.get_line_color()
        self.current_bg_color = self.settings_manager.get_background_color()
        self.current_font = self.settings_manager.get_label_font()

        layout = QVBoxLayout()

        # Группа настроек цветов элементов (AND, OR, XOR, EQUAL, входы, выходы, константы)
        node_colors_group = QGroupBox("Цвета элементов")
        node_colors_layout = QFormLayout()

        # Кнопки выбора цвета для каждого типа элемента
        self.node_color_buttons = {}
        for node_type in self.node_types:
            button = QPushButton()
            button.setFixedSize(50, 30)
            color = self.current_node_colors[node_type]
            button.setStyleSheet(f"background-color: {color.name()};")
            button.clicked.connect(lambda checked, nt=node_type: self.choose_node_color(nt))
            self.node_color_buttons[node_type] = button
            node_colors_layout.addRow(f"{node_type}:", button)

        node_colors_group.setLayout(node_colors_layout)
        layout.addWidget(node_colors_group)

        # Группа настроек цвета линий соединения
        line_color_group = QGroupBox("Цвет линий")
        line_color_layout = QHBoxLayout()
        self.line_color_button = QPushButton()
        self.line_color_button.setFixedSize(50, 30)
        color = self.current_line_color
        self.line_color_button.setStyleSheet(f"background-color: {color.name()};")
        self.line_color_button.clicked.connect(self.choose_line_color)
        line_color_layout.addWidget(QLabel("Цвет:"))
        line_color_layout.addWidget(self.line_color_button)
        line_color_layout.addStretch()
        line_color_group.setLayout(line_color_layout)
        layout.addWidget(line_color_group)

        # Группа настроек цвета фона рабочей области
        bg_color_group = QGroupBox("Цвет фона")
        bg_color_layout = QHBoxLayout()
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedSize(50, 30)
        color = self.current_bg_color
        self.bg_color_button.setStyleSheet(f"background-color: {color.name()};")
        self.bg_color_button.clicked.connect(self.choose_bg_color)
        bg_color_layout.addWidget(QLabel("Цвет:"))
        bg_color_layout.addWidget(self.bg_color_button)
        bg_color_layout.addStretch()
        bg_color_group.setLayout(bg_color_layout)
        layout.addWidget(bg_color_group)

        # Группа настроек размера элементов (ширина и высота узлов)
        size_group = QGroupBox("Размер узлов")
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Ширина:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 200)
        self.width_spin.setValue(self.settings_manager.get_node_size()[0])
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("Высота:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(30, 150)
        self.height_spin.setValue(self.settings_manager.get_node_size()[1])
        size_layout.addWidget(self.height_spin)
        size_layout.addStretch()
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # Группа настроек шрифта для подписей элементов
        font_group = QGroupBox("Шрифт подписей")
        font_layout = QHBoxLayout()
        self.font_button = QPushButton("Выбрать шрифт")
        self.font_label = QLabel()
        font = self.current_font
        self.font_label.setText(f"{font.family()}, {font.pointSize()}pt")
        self.font_label.setFont(font)
        self.font_button.clicked.connect(self.choose_font)
        font_layout.addWidget(self.font_button)
        font_layout.addWidget(self.font_label)
        font_layout.addStretch()
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Кнопки диалога: Ok (применить и закрыть), Cancel (отменить), Apply (применить без закрытия)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Apply)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)

        self.setLayout(layout)

    # Открытие диалога выбора цвета для конкретного типа элемента
    def choose_node_color(self, node_type):
        color = QColorDialog.getColor(self.current_node_colors[node_type], self, f"Выберите цвет для {node_type}")
        if color.isValid():
            self.current_node_colors[node_type] = color
            self.node_color_buttons[node_type].setStyleSheet(f"background-color: {color.name()};")

    # Открытие диалога выбора цвета для линий соединения
    def choose_line_color(self):
        color = QColorDialog.getColor(self.current_line_color, self, "Выберите цвет линий")
        if color.isValid():
            self.current_line_color = color
            self.line_color_button.setStyleSheet(f"background-color: {color.name()};")

    # Открытие диалога выбора цвета фона
    def choose_bg_color(self):
        color = QColorDialog.getColor(self.current_bg_color, self, "Выберите цвет фона")
        if color.isValid():
            self.current_bg_color = color
            self.bg_color_button.setStyleSheet(f"background-color: {color.name()};")

    # Открытие диалога выбора шрифта для подписей
    def choose_font(self):
        font, ok = QFontDialog.getFont(self.current_font, self, "Выберите шрифт")
        if ok:
            self.current_font = font
            self.font_label.setText(f"{font.family()}, {font.pointSize()}pt")
            self.font_label.setFont(font)

    # Применение всех измененных настроек к SettingsManager и сцене
    def apply_settings(self):
        # Сохраняем цвета элементов
        for node_type, color in self.current_node_colors.items():
            self.settings_manager.set_node_color(node_type, color)

        # Сохраняем цвет линий и цвет фона
        self.settings_manager.set_line_color(self.current_line_color)
        self.settings_manager.set_background_color(self.current_bg_color)

        # Сохраняем размер узлов
        width = self.width_spin.value()
        height = self.height_spin.value()
        self.settings_manager.set_node_size(width, height)

        # Сохраняем шрифт подписей
        self.settings_manager.set_label_font(self.current_font)

        # Применяем новые настройки к сцене если она доступна
        if hasattr(self.parent(), 'scene'):
            self.parent().scene.apply_settings()

    # Обработчик нажатия кнопки Ok - применить и закрыть диалог
    def accept(self):
        self.apply_settings()
        super().accept()