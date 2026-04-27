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
            return True
        return False

    def redo(self):
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            return True
        return False

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


class RemoveNodeCommand:
    def __init__(self, circuit, node_id):
        self.circuit = circuit
        self.node_id = node_id
        self.node_data = None
        self.connections = []

    def execute(self):
        node = self.circuit.get_node(self.node_id)
        if node is None:
            return
        self.node_data = node.copy()
        self.connections = [c for c in self.circuit.get_connections() if c[0] == self.node_id or c[2] == self.node_id]
        self.circuit.remove_node(self.node_id)

    def undo(self):
        if self.node_data is None:
            return
        self.circuit.add_node_with_id(self.node_data)
        for conn in self.connections:
            self.circuit.connect_pins(conn[0], conn[1], conn[2], conn[3])


class MoveNodeCommand:
    def __init__(self, circuit, node_id, old_x, old_y, new_x, new_y):
        self.circuit = circuit
        self.node_id = node_id
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y

    def execute(self):
        self.circuit.set_node_position(self.node_id, self.new_x, self.new_y)

    def undo(self):
        self.circuit.set_node_position(self.node_id, self.old_x, self.old_y)


class ConnectPinsCommand:
    def __init__(self, circuit, out_node_id, out_pin, in_node_id, in_pin):
        self.circuit = circuit
        self.out_node_id = out_node_id
        self.out_pin = out_pin
        self.in_node_id = in_node_id
        self.in_pin = in_pin

    def execute(self):
        self.circuit.connect_pins(self.out_node_id, self.out_pin, self.in_node_id, self.in_pin)

    def undo(self):
        self.circuit.disconnect_pins(self.out_node_id, self.out_pin, self.in_node_id, self.in_pin)


class DisconnectPinsCommand:
    def __init__(self, circuit, out_node_id, out_pin, in_node_id, in_pin):
        self.circuit = circuit
        self.out_node_id = out_node_id
        self.out_pin = out_pin
        self.in_node_id = in_node_id
        self.in_pin = in_pin

    def execute(self):
        self.circuit.disconnect_pins(self.out_node_id, self.out_pin, self.in_node_id, self.in_pin)

    def undo(self):
        self.circuit.connect_pins(self.out_node_id, self.out_pin, self.in_node_id, self.in_pin)
