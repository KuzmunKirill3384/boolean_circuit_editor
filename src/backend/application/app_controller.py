from backend.model.circuit import Circuit
from backend.commands.history import CommandHistory
from backend.commands.factory import CommandFactory, CommandFactoryError


class AppController:
    def __init__(self):
        self.circuit = Circuit()
        self.history = CommandHistory()
        self.command_factory = CommandFactory(self.circuit)

    def add_node(self, node_type, x, y):
        cmd = self.command_factory.create_add_node(node_type, x, y)
        self.history.execute(cmd)
        return cmd.node_id

    def remove_node(self, node_id):
        cmd = self.command_factory.create_remove_node(node_id)
        self.history.execute(cmd)

    def move_node(self, node_id, old_x, old_y, new_x, new_y):
        if old_x == new_x and old_y == new_y:
            return
        cmd = self.command_factory.create_move_node(node_id, old_x, old_y, new_x, new_y)
        self.history.execute(cmd)

    def connect_pins(self, out_node_id, out_pin, in_node_id, in_pin):
        try:
            cmd = self.command_factory.create_connect_pins(
                out_node_id, out_pin, in_node_id, in_pin
            )
        except CommandFactoryError as exc:
            return False, str(exc)
        self.history.execute(cmd)
        return True, ""

    def disconnect_pins(self, out_node_id, out_pin, in_node_id, in_pin):
        try:
            cmd = self.command_factory.create_disconnect_pins(
                out_node_id, out_pin, in_node_id, in_pin
            )
        except CommandFactoryError:
            return False
        self.history.execute(cmd)
        return True

    def undo(self):
        return self.history.undo()

    def redo(self):
        return self.history.redo()

    def save_circuit(self, filepath):
        from backend.io.xml_builder import export_to_xml

        export_to_xml(self.circuit, filepath)

    def load_circuit(self, filepath):
        from backend.io.xml_builder import import_from_xml

        self.circuit = import_from_xml(filepath)
        self.command_factory.bind_circuit(self.circuit)
        self.history.clear()

    def get_truth_table(self):
        from backend.logic.truth_table import get_truth_table

        try:
            return get_truth_table(self.circuit)
        except Exception as e:
            return {"inputs": [], "outputs": [], "rows": [], "error": str(e)}

    def get_truth_table_for_node(self, node_id):
        from backend.logic.truth_table import get_truth_table_for_node
        try:
            return get_truth_table_for_node(self.circuit, node_id)
        except Exception as e:
            return {"inputs": [], "node_id": node_id, "rows": [], "error": str(e)}

    def get_affected_nodes(self, node_id):
        from backend.logic.truth_table import get_affected_nodes

        return get_affected_nodes(self.circuit, node_id)

    def get_polynomials(self):
        from backend.logic.truth_table import get_polynomials

        return get_polynomials(self.circuit)

    def get_polynomial_for_node(self, node_id):
        from backend.logic.truth_table import get_polynomial_for_node

        return get_polynomial_for_node(self.circuit, node_id)

    def get_removable_count_per_input(self, input_values=None):
        from backend.logic.truth_table import get_removable_count_per_input

        return get_removable_count_per_input(self.circuit, input_values)

    def simplify_circuit(self, input_values):
        from backend.logic.truth_table import simplify

        self.circuit = simplify(self.circuit, input_values)
        self.command_factory.bind_circuit(self.circuit)
        self.history.clear()

    def evaluate_circuit(self, input_values):
        from backend.logic.truth_table import evaluate_circuit

        return evaluate_circuit(self.circuit, input_values)

    def get_evaluation_report(self, input_values):
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
