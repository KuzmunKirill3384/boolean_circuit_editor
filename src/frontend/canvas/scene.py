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
        self.setSceneRect(0, 0, 1000, 600)
        self.nodes = {}
        self.lines = []

    def set_selected_gate(self, gate_type):
        self.selected_gate = gate_type

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

    def mouseDoubleClickEvent(self, event):
        if self.selected_gate:
            pos = event.scenePos()
            self.controller.add_node(self.selected_gate, pos.x(), pos.y())
            self.sync_scene()
        super().mouseDoubleClickEvent(event)
