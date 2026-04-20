from frontend.core.circuit import Circuit
from frontend.commands.history import (
    CommandHistory,
    AddNodeCommand,
    RemoveNodeCommand,
    MoveNodeCommand,
    ConnectCommand,
    DisconnectCommand,
    ConnectPinsCommand,
    DisconnectPinsCommand,
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

    def connect_pins(self, out_node_id, out_pin, in_node_id, in_pin):
        success, message = self.circuit.connect_pins(out_node_id, out_pin, in_node_id, in_pin)
        if success:
            cmd = ConnectPinsCommand(self.circuit, out_node_id, out_pin, in_node_id, in_pin)
            self.history.execute(cmd)
        return success, message

    def disconnect_pins(self, out_node_id, out_pin, in_node_id, in_pin):
        success = self.circuit.disconnect_pins(out_node_id, out_pin, in_node_id, in_pin)
        if success:
            cmd = DisconnectPinsCommand(self.circuit, out_node_id, out_pin, in_node_id, in_pin)
            self.history.execute(cmd)
        return success
    
    def undo(self):
        return self.history.undo()

    def redo(self):
        return self.history.redo()

    def save_circuit(self, filepath):
        try:
            from frontend.core.builder import export_to_xml
            export_to_xml(self.circuit, filepath)
        except Exception as e:
            print("Ошибка при сохранении:", e)
            raise

    def load_circuit(self, filepath):
        try:
            from frontend.core.builder import import_from_xml
            self.circuit = import_from_xml(filepath)
            self.history.clear()
        except Exception as e:
            print("Ошибка при загрузке:", e)

    def get_truth_table(self):
        try:
            from backend.logic.truth_table import get_truth_table
            return get_truth_table(self.circuit)
        except Exception:
            return {"inputs": [], "outputs": [], "rows": []}

    def get_truth_table_for_node(self, node_id):
        try:
            from backend.logic.truth_table import get_truth_table_for_node
            try:
                return get_truth_table_for_node(self.circuit, node_id)
            except TypeError:
                return get_truth_table_for_node(node_id)
        except Exception:
            return {"inputs": [], "node_id": node_id, "rows": []}

    def get_affected_nodes(self, node_id):
        try:
            from backend.logic.truth_table import get_affected_nodes
            try:
                return get_affected_nodes(self.circuit, node_id)
            except TypeError:
                return get_affected_nodes(node_id)
        except Exception:
            return []

    def get_polynomials(self):
        try:
            from backend.logic.truth_table import get_polynomials
            return get_polynomials(self.circuit)
        except Exception:
            return None

    def get_polynomial_for_node(self, node_id):
        try:
            from backend.logic.truth_table import get_polynomial_for_node
            try:
                return get_polynomial_for_node(self.circuit, node_id)
            except TypeError:
                return get_polynomial_for_node(node_id)
        except Exception:
            return None

    def get_removable_count_per_input(self, input_values):
        try:
            from backend.logic.truth_table import get_removable_count_per_input
            return get_removable_count_per_input(self.circuit, input_values)
        except Exception:
            return {}

    def simplify_circuit(self, input_values):
        try:
            from backend.logic.truth_table import simplify
            self.circuit = simplify(self.circuit, input_values)
            self.history.clear()
        except Exception:
            pass

    def evaluate_circuit(self, input_values):
        try:
            from backend.logic.truth_table import evaluate_circuit
            return evaluate_circuit(self.circuit, input_values)
        except Exception:
            return {}

    def get_evaluation_report(self, input_values):
        try:
            report = {}
            tt = self.get_truth_table()
            if tt and tt.get("inputs"):
                for row in tt.get("rows", []):
                    match = True
                    for inp_id in tt.get("inputs", []):
                        if row.get(f"IN_{inp_id}") != input_values.get(inp_id):
                            match = False
                            break
                    if match:
                        report["row"] = row
                        break
            return report
        except Exception:
            return {}
