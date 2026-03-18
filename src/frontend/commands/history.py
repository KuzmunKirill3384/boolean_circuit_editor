# frontend/commands/history.py

class CommandHistory:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def execute(self, command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)

    def redo(self):
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()


class AddNodeCommand:
    def __init__(self, circuit, node_type, x, y):
        self.circuit = circuit
        self.node_type = node_type
        self.x = x
        self.y = y
        self.node_id = None

    def execute(self):
        self.node_id = self.circuit.add_node(self.node_type, self.x, self.y)

    def undo(self):
        if self.node_id is not None:
            self.circuit.remove_node(self.node_id)


class ConnectCommand:
    def __init__(self, circuit, out_node_id, in_node_id):
        self.circuit = circuit
        self.out_node_id = out_node_id
        self.in_node_id = in_node_id

    def execute(self):
        self.circuit.connect_nodes(self.out_node_id, self.in_node_id)

    def undo(self):
        self.circuit.disconnect_nodes(self.out_node_id, self.in_node_id)
