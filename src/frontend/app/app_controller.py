from frontend.core.circuit import Circuit
from frontend.commands.history import (
    CommandHistory,
    AddNodeCommand,
    RemoveNodeCommand,
    MoveNodeCommand,
    ConnectCommand,
    DisconnectCommand,
)

class AppController:
    def __init__(self):
        self.circuit = Circuit()
        self.history = CommandHistory()

    def add_node(self, node_type, x, y):
        cmd = AddNodeCommand(self.circuit, node_type, x, y)
        self.history.execute(cmd)
        return cmd.node_id

    def remove_node(self, node_id):
        cmd = RemoveNodeCommand(self.circuit, node_id)
        self.history.execute(cmd)

    def move_node(self, node_id, old_x, old_y, new_x, new_y):
        if old_x == new_x and old_y == new_y:
            return
        cmd = MoveNodeCommand(self.circuit, node_id, old_x, old_y, new_x, new_y)
        self.history.execute(cmd)

    def connect_nodes(self, out_node_id, in_node_id):
        cmd = ConnectCommand(self.circuit, out_node_id, in_node_id)
        self.history.execute(cmd)

    def disconnect_nodes(self, out_node_id, in_node_id):
        cmd = DisconnectCommand(self.circuit, out_node_id, in_node_id)
        self.history.execute(cmd)

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

    # def get_truth_table(self):
    #     from backend.logic.truth_table import get_truth_table
    #     return get_truth_table(self.circuit)

    # def get_truth_table_for_node(self, node_id):
    #     from backend.logic.truth_table import get_truth_table_for_node
    #     return get_truth_table_for_node(self.circuit, node_id)

    # def get_affected_nodes(self, node_id):
    #     from backend.logic.truth_table import get_affected_nodes
    #     return get_affected_nodes(self.circuit, node_id)
