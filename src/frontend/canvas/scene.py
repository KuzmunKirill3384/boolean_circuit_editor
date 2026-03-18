from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem
from PyQt6.QtGui import QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt


class NodeItem(QGraphicsRectItem):
    WIDTH = 95
    HEIGHT = 50

    def __init__(self, node, move_callback=None):
        super().__init__(-NodeItem.WIDTH / 2, -NodeItem.HEIGHT / 2, NodeItem.WIDTH, NodeItem.HEIGHT)
        self.node_id = node["id"]
        self.node_type = node["type"]
        self.move_callback = move_callback
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{self.node_type} ({self.node_id})")
        self.setPos(node["x"], node["y"])

    def paint(self, painter, option, widget=None):
        color_map = {
            "AND": QColor("#6c7ae0"),
            "OR": QColor("#edc126"),
            "XOR": QColor("#8cd17a"),
            "EQUAL": QColor("#ef6d6d"),
            "IN": QColor("#8fbcff"),
            "OUT": QColor("#a68cfc"),
        }
        color = color_map.get(self.node_type.upper(), QColor("#999999"))
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawRoundedRect(self.rect(), 8, 8)

        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.node_type}\n#{self.node_id}")

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged and self.move_callback:
            self.move_callback(self.node_id, value.x(), value.y())
        return super().itemChange(change, value)


from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem


class ConnectionLine(QGraphicsLineItem):
    def __init__(self, from_item, to_item):
        super().__init__()
        self.from_item = from_item
        self.to_item = to_item
        self.setZValue(-1)
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.update_line()

    def update_line(self):
        p1 = self.from_item.scenePos()
        p2 = self.to_item.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())


class CircuitScene(QGraphicsScene):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected_gate = None
        self.mode = "add"
        self.connect_source_id = None
        self.setSceneRect(0, 0, 1000, 600)
        self.nodes = {}
        self.lines = []

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
            item = NodeItem(node, move_callback=self.on_node_moved)
            self.addItem(item)
            self.nodes[node["id"]] = item

        for out_id, in_id in self.controller.circuit.get_connections():
            from_item = self.nodes.get(out_id)
            to_item = self.nodes.get(in_id)
            if from_item is None or to_item is None:
                continue
            line = ConnectionLine(from_item, to_item)
            self.addItem(line)
            self.lines.append(line)

    def on_node_moved(self, node_id, x, y):
        self.controller.move_node(node_id, x, y)
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
                    from frontend.commands.history import ConnectCommand
                    cmd = ConnectCommand(self.controller.circuit, self.connect_source_id, dest_id)
                    self.controller.history.execute(cmd)
                    print(f"Соединено {self.connect_source_id} -> {dest_id}")
                    self.sync_scene()
                else:
                    print("Ошибка валидации связи:", reason)
                self.connect_source_id = None
            return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
