from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QPainter  # для RenderHint

class CircuitView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        # Включаем или отключаем антиалиасинг (сглаживание)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        # Режим выделения объектов рамкой
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)