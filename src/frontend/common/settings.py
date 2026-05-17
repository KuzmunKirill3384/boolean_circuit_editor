from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

  
class SettingsManager:
    """Класс для управления настройками внешнего вида приложения, такими как цвета элементов, шрифты и размеры. 
    Использует QSettings для сохранения и загрузки настроек между сессиями."""
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
    
   
    def set_node_color(self, node_type, color):
        """Устанавливает цвет для заданного типа узла и сохраняет его в настройках."""
        self.settings.setValue(f"node_colors/{node_type}", color.name())
  
    def get_line_color(self):
        """Получает цвет линий, соединяющих узлы, из настроек или возвращает черный по умолчанию."""
        color_str = self.settings.value("line_color", QColor(Qt.GlobalColor.black).name())
        return QColor(color_str)

    def set_line_color(self, color):
        """Устанавливает цвет линий соединения и сохраняет его в настройках."""
        self.settings.setValue("line_color", color.name())

    def get_background_color(self):
        """Получает цвет фона рабочего пространства из настроек или возвращает белый по умолчанию."""
        color_str = self.settings.value("background_color", QColor(Qt.GlobalColor.white).name())
        return QColor(color_str)

    def set_background_color(self, color):
        """Устанавливает цвет фона рабочего пространства и сохраняет его в настройках."""
        self.settings.setValue("background_color", color.name())

    def get_node_size(self):
        """Получает размеры узлов (ширина и высота) из настроек или возвращает 95x50 по умолчанию."""
        width = int(self.settings.value("node_width", 95))
        height = int(self.settings.value("node_height", 50))
        return width, height

    def set_node_size(self, width, height):
        """Устанавливает размеры узлов (ширина и высота) и сохраняет их в настройках."""
        self.settings.setValue("node_width", width)
        self.settings.setValue("node_height", height)

    def get_label_font(self):
        """Получает шрифт для подписей узлов из настроек или возвращает Arial 9pt по умолчанию."""
        family = self.settings.value("font_family", "Arial")
        size = int(self.settings.value("font_size", 9))
        return QFont(family, size)

    def set_label_font(self, font):
        """Устанавливает шрифт для подписей узлов и сохраняет его в настройках."""
        self.settings.setValue("font_family", font.family())
        self.settings.setValue("font_size", font.pointSize())