from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

# Класс для управления настройками приложения    
class SettingsManager:
    def __init__(self):
        self.settings = QSettings("BooleanCircuitEditor", "Settings")

    def get_node_color(self, node_type):
        default_colors = {
            "AND": QColor("#6c7ae0"),
            "OR": QColor("#edc126"),
            "XOR": QColor("#8cd17a"),
            "EQUAL": QColor("#ef6d6d"),
            "IN": QColor("#8fbcff"),
            "OUT": QColor("#a68cfc"),
            "CONST_0": QColor("#ffb3ba"),
            "CONST_1": QColor("#bae1ff"),
        }
        color_str = self.settings.value(f"node_colors/{node_type}", default_colors.get(node_type.upper(), QColor("#999999")).name())
        return QColor(color_str)
    
    # Метод для установки цвета для конкретного типа узла
    def set_node_color(self, node_type, color):
        self.settings.setValue(f"node_colors/{node_type}", color.name())
    # Метод для получения цвета линий, соединяющих узлы
    def get_line_color(self):
        color_str = self.settings.value("line_color", QColor(Qt.GlobalColor.black).name())
        return QColor(color_str)
    # Метод для установки цвета линий, соединяющих узлы
    def set_line_color(self, color):
        self.settings.setValue("line_color", color.name())
    # Метод для получения цвета фона рабочего пространства
    def get_background_color(self):
        color_str = self.settings.value("background_color", QColor(Qt.GlobalColor.white).name())
        return QColor(color_str)
    # Метод для установки цвета фона рабочего пространства
    def set_background_color(self, color):
        self.settings.setValue("background_color", color.name())
    # Метод для получения размера узлов
    def get_node_size(self):
        width = int(self.settings.value("node_width", 95))
        height = int(self.settings.value("node_height", 50))
        return width, height
    # Метод для установки размера узлов
    def set_node_size(self, width, height):
        self.settings.setValue("node_width", width)
        self.settings.setValue("node_height", height)
    # Метод для получения шрифта, используемого в узлах
    def get_label_font(self):
        family = self.settings.value("font_family", "Arial")
        size = int(self.settings.value("font_size", 9))
        return QFont(family, size)
    # Метод для установки шрифта, используемого в узлах
    def set_label_font(self, font):
        self.settings.setValue("font_family", font.family())
        self.settings.setValue("font_size", font.pointSize())