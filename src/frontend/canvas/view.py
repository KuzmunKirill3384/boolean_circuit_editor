from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView

# Класс для отображения сцены с поддержкой масштабирования и навигации
class CircuitView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._panning = False

    # Масштабирование колесиком мыши
    def wheelEvent(self, event):
        zoom_in = 1.15
        zoom_out = 1 / zoom_in
        factor = zoom_in if event.angleDelta().y() > 0 else zoom_out
        self.scale(factor, factor)

    # Панорамирование сцены средней кнопкой мыши
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    # Окончание панорамирования
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # Обработка клавиш: навигация, масштабирование
    def keyPressEvent(self, event):
        step = 60
        if event.key() == Qt.Key.Key_Left:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - step)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Right:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + step)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Up:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - step)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Down:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + step)
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.scale(1.15, 1.15)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Minus:
            self.scale(1 / 1.15, 1 / 1.15)
            event.accept()
            return
        super().keyPressEvent(event)