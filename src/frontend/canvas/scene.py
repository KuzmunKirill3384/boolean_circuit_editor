from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem
from PyQt6.QtGui import QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt
from frontend.common.settings import SettingsManager


class NodeItem(QGraphicsRectItem):
    def __init__(self, node, move_callback=None, settings_manager=None):
        self.settings_manager = settings_manager or SettingsManager()
        width, height = self.settings_manager.get_node_size()
        super().__init__(-width / 2, -height / 2, width, height)
        self.node_id = node["id"]
        self.node_type = node["type"]
        self.move_callback = move_callback
        self.highlight_status = "default"
        self.original_pos = (node["x"], node["y"])
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{self.node_type} ({self.node_id})")
        self.setPos(node["x"], node["y"])

    def set_highlight(self, status):
        self.highlight_status = status
        self.update()

    def paint(self, painter, option, widget=None):
        color = self.settings_manager.get_node_color(self.node_type.upper())
        if self.highlight_status == "affected":
            color = QColor("#ff8c00")
        elif self.highlight_status == "selected":
            color = QColor("#34c759")
        painter.setBrush(QBrush(color))
        pen_color = Qt.GlobalColor.black
        if self.isSelected():
            pen_color = Qt.GlobalColor.red
        painter.setPen(QPen(pen_color, 2))
        painter.drawRoundedRect(self.rect(), 8, 8)

        font = self.settings_manager.get_label_font()
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.node_type}\n#{self.node_id}")

    def mousePressEvent(self, event):
        self.original_pos = (self.x(), self.y())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.move_callback:
            new_x = self.x()
            new_y = self.y()
            old_x, old_y = self.original_pos
            if old_x != new_x or old_y != new_y:
                self.move_callback(self.node_id, old_x, old_y, new_x, new_y)

class ConnectionLine(QGraphicsLineItem):
    def __init__(self, from_item, to_item, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager or SettingsManager()
        self.from_item = from_item
        self.to_item = to_item
        self.setZValue(-1)
        self.update_pen()
        self.update_line()

    def update_pen(self):
        color = self.settings_manager.get_line_color()
        self.setPen(QPen(color, 2))

    def update_line(self):
        p1 = self.from_item.scenePos()
        p2 = self.to_item.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())


class CircuitScene(QGraphicsScene):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.settings_manager = SettingsManager()
        self.selected_gate = None
        self.mode = "add"
        self.connect_source_id = None
        self.setSceneRect(0, 0, 1000, 600)
        self.nodes = {}
        self.lines = []
        self.apply_settings()

    def set_selected_gate(self, gate_type):
        self.selected_gate = gate_type
        self.mode = "add"
        self.connect_source_id = None

    def set_connect_mode(self):
        self.mode = "connect"
        self.connect_source_id = None

    def sync_scene(self):
        self.clear()
        self.nodes = {}
        self.lines = []

        for node in self.controller.circuit.get_nodes():
            item = NodeItem(node, move_callback=self.on_node_moved, settings_manager=self.settings_manager)
            self.addItem(item)
            self.nodes[node["id"]] = item

        for out_id, in_id in self.controller.circuit.get_connections():
            from_item = self.nodes.get(out_id)
            to_item = self.nodes.get(in_id)
            if from_item is None or to_item is None:
                continue
            line = ConnectionLine(from_item, to_item, settings_manager=self.settings_manager)
            self.addItem(line)
            self.lines.append(line)

    def apply_settings(self):
        bg_color = self.settings_manager.get_background_color()
        self.setBackgroundBrush(QBrush(bg_color))
        # Пересинхронизировать сцену для применения новых размеров и цветов
        self.sync_scene()

    def on_node_moved(self, node_id, old_x, old_y, new_x, new_y):
        self.controller.move_node(node_id, old_x, old_y, new_x, new_y)
        for line in self.lines:
            line.update_line()

    def validate_connection(self, out_id, in_id):
        if out_id == in_id:
            return False, "Нельзя соединить узел сам с собой"
        if not self.controller.circuit.get_node(out_id) or not self.controller.circuit.get_node(in_id):
            return False, "Узел не найден"
        if (out_id, in_id) in self.controller.circuit.get_connections():
            return False, "Соединение уже существует"
        return True, "OK"

    def highlight_nodes(self, node_ids, selected_node_id=None):
        selected_node_id = selected_node_id
        for node_id, item in self.nodes.items():
            if node_id in node_ids:
                status = "selected" if node_id == selected_node_id else "affected"
                item.set_highlight(status)
            else:
                item.set_highlight("default")

    def clear_highlights(self):
        for item in self.nodes.values():
            item.set_highlight("default")

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        scene_pos = event.scenePos()
        clicked_items = self.items(scene_pos)
        clicked_node = None
        for item in clicked_items:
            if isinstance(item, NodeItem):
                clicked_node = item
                break

        if self.mode == "add" and self.selected_gate and clicked_node is None:
            node_id = self.controller.add_node(self.selected_gate, scene_pos.x(), scene_pos.y())
            print(f"Добавлен узел {self.selected_gate} id={node_id} в {scene_pos.x():.1f},{scene_pos.y():.1f}")
            self.sync_scene()
            return

        if self.mode == "connect":
            if clicked_node is None:
                super().mousePressEvent(event)
                return
            if self.connect_source_id is None:
                self.connect_source_id = clicked_node.node_id
                print(f"Режим связи: выбран исходный узел {self.connect_source_id}")
            else:
                dest_id = clicked_node.node_id
                valid, reason = self.validate_connection(self.connect_source_id, dest_id)
                if valid:
                    self.controller.connect_nodes(self.connect_source_id, dest_id)
                    print(f"Соединено {self.connect_source_id} -> {dest_id}")
                    self.sync_scene()
                else:
                    print("Ошибка валидации связи:", reason)
                self.connect_source_id = None
            return

        if self.mode == "disconnect":
            if clicked_node is None:
                super().mousePressEvent(event)
                return
            if self.connect_source_id is None:
                self.connect_source_id = clicked_node.node_id
                print(f"Режим отключения: выбран исходный узел {self.connect_source_id}")
            else:
                dest_id = clicked_node.node_id
                if (self.connect_source_id, dest_id) in self.controller.circuit.get_connections():
                    self.controller.disconnect_nodes(self.connect_source_id, dest_id)
                    print(f"Отключено {self.connect_source_id} -> {dest_id}")
                    self.sync_scene()
                else:
                    print("Связь не найдена для отключения")
                self.connect_source_id = None
            return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            selected_items = self.selectedItems()
            for item in selected_items:
                if isinstance(item, NodeItem):
                    self.controller.remove_node(item.node_id)
                    print(f"Узел {item.node_id} удален")
            self.sync_scene()
            return
        super().keyPressEvent(event)
