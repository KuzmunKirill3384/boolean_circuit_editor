from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QGroupBox, QFormLayout
from PyQt6.QtCore import pyqtSignal

class PropertiesPanel(QWidget):
    properties_changed = pyqtSignal(dict) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_node = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Properties")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        self.node_group = QGroupBox("Node")
        node_layout = QFormLayout()
        
        self.id_label = QLabel("-")
        self.type_label = QLabel("-")
        self.x_edit = QLineEdit()
        self.y_edit = QLineEdit()
        
        node_layout.addRow("ID:", self.id_label)
        node_layout.addRow("Type:", self.type_label)
        node_layout.addRow("X:", self.x_edit)
        node_layout.addRow("Y:", self.y_edit)
        
        self.node_group.setLayout(node_layout)
        layout.addWidget(self.node_group)

        self.connections_label = QLabel("Connections: -")
        layout.addWidget(self.connections_label)
        
        layout.addStretch()

        self.x_edit.editingFinished.connect(self.on_position_changed)
        self.y_edit.editingFinished.connect(self.on_position_changed)

    def set_selected_node(self, node_data, circuit):
        self.selected_node = node_data
        if node_data:
            self.id_label.setText(str(node_data["id"]))
            self.type_label.setText(node_data["type"])
            self.x_edit.setText(str(node_data["x"]))
            self.y_edit.setText(str(node_data["y"]))

            connections = circuit.get_connections()
            input_count = sum(1 for c in connections if c[2] == node_data["id"])
            output_count = sum(1 for c in connections if c[0] == node_data["id"])
            self.connections_label.setText(f"Connections: {input_count} in, {output_count} out")
            
            self.node_group.setEnabled(True)
        else:
            self.id_label.setText("-")
            self.type_label.setText("-")
            self.x_edit.setText("")
            self.y_edit.setText("")
            self.connections_label.setText("Connections: -")
            self.node_group.setEnabled(False)

    def on_position_changed(self):
        if not self.selected_node:
            return
        try:
            new_x = float(self.x_edit.text())
            new_y = float(self.y_edit.text())
            old_x = self.selected_node["x"]
            old_y = self.selected_node["y"]
            if old_x != new_x or old_y != new_y:
                self.properties_changed.emit({
                    "action": "move_node",
                    "node_id": self.selected_node["id"],
                    "old_x": old_x,
                    "old_y": old_y,
                    "new_x": new_x,
                    "new_y": new_y
                })
        except ValueError:
            self.x_edit.setText(str(self.selected_node["x"]))
            self.y_edit.setText(str(self.selected_node["y"]))