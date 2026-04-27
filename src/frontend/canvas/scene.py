from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem
from PyQt6.QtGui import QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, QTimer
from frontend.common.settings import SettingsManager
from backend.model.circuit import Circuit


class PinItem(QGraphicsEllipseItem):
    def __init__(self, node_item, pin_index, is_input, settings_manager=None):
        self.settings_manager = settings_manager or SettingsManager()
        size = 10
        super().__init__(-size/2, -size/2, size, size)
        self.node_item = node_item
        self.pin_index = pin_index
        self.is_input = is_input
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{'Input' if is_input else 'Output'} pin {pin_index}")
        self._selected_for_link = False

    def hoverEnterEvent(self, event):
        self.setPen(QPen(Qt.GlobalColor.blue, 2))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self._selected_for_link:
            self.setPen(QPen(QColor("#34c759"), 3))
        else:
            self.setPen(QPen(Qt.GlobalColor.black, 1))
        super().hoverLeaveEvent(event)

    def set_link_selected(self, selected: bool):
        self._selected_for_link = selected
        if selected:
            self.setPen(QPen(QColor("#34c759"), 3))
            self.setBrush(QBrush(QColor("#d1fadf")))
        else:
            self.setPen(QPen(Qt.GlobalColor.black, 1))
            self.setBrush(QBrush(Qt.GlobalColor.white))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.scene():
            self.scene().on_pin_clicked(self.node_item.node_id, self.pin_index, self.is_input)
            event.accept()
            return
        super().mousePressEvent(event)


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
        self.pins = []
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{self.node_type} ({self.node_id})")
        self.setPos(node["x"], node["y"])
        self.create_pins()

    def create_pins(self):
        input_pins, output_pins = Circuit.get_pin_counts(self.node_type)
        width, height = self.settings_manager.get_node_size()
        
        for i in range(input_pins):
            y_offset = (i - (input_pins - 1) / 2) * 20
            pin = PinItem(self, i, True, self.settings_manager)
            pin.setPos(-width/2 - 4, y_offset)
            pin.setParentItem(self)
            self.pins.append(pin)
        
        for i in range(output_pins):
            y_offset = (i - (output_pins - 1) / 2) * 20
            pin = PinItem(self, i, False, self.settings_manager)
            pin.setPos(width/2 + 4, y_offset)
            pin.setParentItem(self)
            self.pins.append(pin)

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

        
        if self.node_type.upper() == "AND":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 4)  
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "∧")
        elif self.node_type.upper() == "OR":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 4)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "∨")
        elif self.node_type.upper() == "XOR":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 22)
            painter.setFont(font)
            text_rect = self.rect().adjusted(0, 0, 0, -7)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "⊕")
        elif self.node_type.upper() == "EQUAL":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 20)
            painter.setFont(font)
            text_rect = self.rect().adjusted(0, 0, 0, -7)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "=")
        elif self.node_type.upper() == "IN":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 4)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "▶")
        elif self.node_type.upper() == "OUT":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 4)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "◀")
        elif self.node_type.upper() == "CONST_0":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 6)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "0")
        elif self.node_type.upper() == "CONST_1":
            painter.drawRoundedRect(self.rect(), 8, 8)
            painter.setPen(Qt.GlobalColor.white)
            font = self.settings_manager.get_label_font()
            font.setPointSize(font.pointSize() + 6)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "1")
        else:
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
    def __init__(self, from_pin, to_pin, scene=None, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager or SettingsManager()
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.scene_ref = scene
        self.setZValue(-1)
        self.setAcceptHoverEvents(True)
        self.is_hovered = False
        self.update_pen()
        self.update_line()

    def hoverEnterEvent(self, event):
        if self.scene_ref and self.scene_ref.mode == "disconnect":
            self.setPen(QPen(QColor("#ff0000"), 3))
        else:
            self.setPen(QPen(QColor("#ffa500"), 3))
        self.is_hovered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update_pen()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.scene_ref and self.scene_ref.mode == "disconnect":
            success = self.scene_ref.controller.disconnect_pins(
                self.from_pin.node_item.node_id,
                self.from_pin.pin_index,
                self.to_pin.node_item.node_id,
                self.to_pin.pin_index
            )
            if success:
                QTimer.singleShot(0, self.scene_ref.sync_scene)
            event.accept()
            return
        super().mousePressEvent(event)

    def update_pen(self):
        if self.is_hovered:
            return  
        color = self.settings_manager.get_line_color()
        self.setPen(QPen(color, 2))

    def update_line(self):
        p1 = self.from_pin.scenePos()
        p2 = self.to_pin.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())


class CircuitScene(QGraphicsScene):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.settings_manager = SettingsManager()
        self.selected_gate = None
        self.mode = "add"
        self.connect_source_id = None
        self.temp_line = None
        self.setSceneRect(0, 0, 1000, 600)
        self.nodes = {}
        self.lines = []
        self.apply_settings()

    def _clear_connect_selection(self):
        if self.connect_source_id is None:
            return
        node_id, pin_index, is_input = self.connect_source_id
        node = self.nodes.get(node_id)
        if not node:
            self.connect_source_id = None
            return
        for pin in node.pins:
            if pin.pin_index == pin_index and pin.is_input == is_input:
                pin.set_link_selected(False)
                break
        self.connect_source_id = None

    def set_selected_gate(self, gate_type):
        self.selected_gate = gate_type
        self.mode = "add"
        self._clear_connect_selection()
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

    def set_connect_mode(self):
        self.mode = "connect"
        self._clear_connect_selection()
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

    def set_disconnect_mode(self):
        self.mode = "disconnect"
        self._clear_connect_selection()
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

    def on_pin_clicked(self, node_id, pin_index, is_input):

        if self.mode == "connect":
            if self.connect_source_id is None:
              
                if is_input:
                    return  
                self.connect_source_id = (node_id, pin_index, is_input)
                node = self.nodes.get(node_id)
                if node:
                    for pin in node.pins:
                        if pin.pin_index == pin_index and pin.is_input == is_input:
                            pin.set_link_selected(True)
                            break
            else:
                
                source_node, source_pin, source_is_input = self.connect_source_id
                if source_node == node_id and source_pin == pin_index:
                    return  
            
                if not is_input:
                    return 
                
                success, message = self.controller.connect_pins(source_node, source_pin, node_id, pin_index)
                if success:
    
                    QTimer.singleShot(0, self.sync_scene)
                
                self._clear_connect_selection()
                if self.temp_line:
                    self.removeItem(self.temp_line)
                    self.temp_line = None
            return

        if self.mode == "disconnect":
            if self.connect_source_id is None:
                
                if is_input:
                    return 
                self.connect_source_id = (node_id, pin_index, is_input)
            else:
                
                source_node, source_pin, source_is_input = self.connect_source_id
                
                if not is_input:
                    self.connect_source_id = (node_id, pin_index, is_input)
                    return
                
                success = self.controller.disconnect_pins(source_node, source_pin, node_id, pin_index)
                if success:
                    QTimer.singleShot(0, self.sync_scene)
                
                self._clear_connect_selection()
            return

    def sync_scene(self):
        self.clear()
        self.nodes = {}
        self.lines = []

        for node in self.controller.circuit.get_nodes():
            item = NodeItem(node, move_callback=self.on_node_moved, settings_manager=self.settings_manager)
            self.addItem(item)
            self.nodes[node["id"]] = item

        for out_id, out_pin, in_id, in_pin in self.controller.circuit.get_connections():
            from_node = self.nodes.get(out_id)
            to_node = self.nodes.get(in_id)
            if from_node is None or to_node is None:
                continue
            from_pin = None
            to_pin = None
            for pin in from_node.pins:
                if not pin.is_input and pin.pin_index == out_pin:
                    from_pin = pin
                    break
            for pin in to_node.pins:
                if pin.is_input and pin.pin_index == in_pin:
                    to_pin = pin
                    break
            if from_pin and to_pin:
                line = ConnectionLine(from_pin, to_pin, scene=self, settings_manager=self.settings_manager)
                self.addItem(line)
                self.lines.append(line)

    def apply_settings(self):
        bg_color = self.settings_manager.get_background_color()
        self.setBackgroundBrush(QBrush(bg_color))
        self.sync_scene()

    def on_node_moved(self, node_id, old_x, old_y, new_x, new_y):
        self.controller.move_node(node_id, old_x, old_y, new_x, new_y)
        for line in self.lines:
            line.update_line()

    def highlight_nodes(self, node_ids, selected_node_id=None):
        selected_node_id = selected_node_id
        for node_id, item in self.nodes.items():
            try:
                if item.scene() is not None:
                    if node_id in node_ids:
                        status = "selected" if node_id == selected_node_id else "affected"
                        item.set_highlight(status)
                    else:
                        item.set_highlight("default")
            except RuntimeError:
                pass

    def clear_highlights(self):
        for item in self.nodes.values():
            try:
                if item.scene() is not None:
                    item.set_highlight("default")
            except RuntimeError:
                pass

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
            self.sync_scene()
            return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)

    def delete_selected_nodes(self):
        selected_items = self.selectedItems()
        removed_any = False
        for item in selected_items:
            if isinstance(item, NodeItem):
                self.controller.remove_node(item.node_id)
                removed_any = True
        if removed_any:
            self.sync_scene()
        return removed_any

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected_nodes()
            return
        super().keyPressEvent(event)
