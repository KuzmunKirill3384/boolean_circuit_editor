# app/app_controller.py
from core.circuit import Circuit
from commands.history import CommandHistory, AddNodeCommand, ConnectCommand

class AppController:
    def __init__(self):
        self.circuit = Circuit()
        self.history = CommandHistory()

    def add_node(self, node_type, x, y):
        cmd = AddNodeCommand(self.circuit, node_type, x, y)
        self.history.execute(cmd)

    def move_node(self, node_id, new_x, new_y):
        pass

    def connect_nodes(self, out_node_id, in_node_id):
        cmd = ConnectCommand(self.circuit, out_node_id, in_node_id)
        self.history.execute(cmd)

    def disconnect_nodes(self, out_node_id, in_node_id):
        pass

    def undo(self):
        self.history.undo()

    def redo(self):
        self.history.redo()

    def save_circuit(self, filepath):
        try:
            from core.builder import export_to_xml
            export_to_xml(self.circuit, filepath)
        except Exception as e:
            print("Ошибка при сохранении:", e)

    def load_circuit(self, filepath):
        try:
            from core.builder import import_from_xml
            self.circuit = import_from_xml(filepath)
            self.history.clear()
        except Exception as e:
            print("Ошибка при загрузке:", e)