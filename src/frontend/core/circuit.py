
class Circuit:
    def __init__(self):
        self.nodes = [] 
        self.connections = []
        self._next_node_id = 0 

    @staticmethod
    def get_pin_counts(node_type):
        """Return (input_pins, output_pins) for the node type"""
        pin_counts = {
            "AND": (2, 1),
            "OR": (2, 1),
            "XOR": (2, 1),
            "EQUAL": (2, 1),
            "IN": (0, 1),
            "OUT": (1, 0),
            "CONST_0": (0, 1),
            "CONST_1": (0, 1)
        }
        return pin_counts.get(node_type.upper(), (1, 1))  # Default 1 in, 1 out

    def add_node(self, node_type, x, y):
        node = {
            "id": self._next_node_id,
            "type": node_type,
            "x": float(x),
            "y": float(y)
        }
        self.nodes.append(node)
        self._next_node_id += 1
        return node["id"]

    def add_node_with_id(self, node):
        self.nodes.append(node)
        self._next_node_id = max(self._next_node_id, node["id"] + 1)

    def remove_node(self, node_id):
        self.nodes = [n for n in self.nodes if n["id"] != node_id]
        self.connections = [c for c in self.connections if c[0] != node_id and c[2] != node_id]

    def set_node_position(self, node_id, x, y):
        for node in self.nodes:
            if node["id"] == node_id:
                node["x"] = float(x)
                node["y"] = float(y)
                return True
        return False

    def validate_connection(self, out_node_id, out_pin, in_node_id, in_pin):
        """Validate if a connection can be made"""
        if out_node_id == in_node_id:
            return False, "Cannot connect node to itself"
        
        out_node = self.get_node(out_node_id)
        in_node = self.get_node(in_node_id)
        if not out_node or not in_node:
            return False, "Node not found"
        
        out_input_pins, out_output_pins = self.get_pin_counts(out_node["type"])
        in_input_pins, in_output_pins = self.get_pin_counts(in_node["type"])
        
        if out_pin >= out_output_pins:
            return False, f"Output pin {out_pin} does not exist on {out_node['type']}"
        if in_pin >= in_input_pins:
            return False, f"Input pin {in_pin} does not exist on {in_node['type']}"
        
        # Check if input pin is already connected
        for conn in self.connections:
            if conn[2] == in_node_id and conn[3] == in_pin:
                return False, f"Input pin {in_pin} is already connected"
        
        # Check for cycles (simple check: if in_node connects back to out_node)
        if self.would_create_cycle(out_node_id, in_node_id):
            return False, "Connection would create a cycle"
        
        return True, ""

    def would_create_cycle(self, start_id, end_id):
        """Check if connecting start to end would create a cycle"""
        visited = set()
        def dfs(node_id):
            if node_id in visited:
                return False
            visited.add(node_id)
            for conn in self.connections:
                if conn[0] == node_id:
                    if conn[2] == end_id:
                        return True
                    if dfs(conn[2]):
                        return True
            return False
        return dfs(start_id)

    def connect_pins(self, out_node_id, out_pin, in_node_id, in_pin):
        valid, reason = self.validate_connection(out_node_id, out_pin, in_node_id, in_pin)
        if not valid:
            return False, reason
        connection = (out_node_id, out_pin, in_node_id, in_pin)
        if connection in self.connections:
            return False, "Connection already exists"
        self.connections.append(connection)
        return True, ""

    def disconnect_pins(self, out_node_id, out_pin, in_node_id, in_pin):
        connection = (out_node_id, out_pin, in_node_id, in_pin)
        if connection in self.connections:
            self.connections.remove(connection)
            return True
        return False

    # Legacy methods for backward compatibility (but deprecated)
    def connect_nodes(self, out_node_id, in_node_id):
        # Assume pin 0 for both
        return self.connect_pins(out_node_id, 0, in_node_id, 0)

    def disconnect_nodes(self, out_node_id, in_node_id):
        self.disconnect_pins(out_node_id, 0, in_node_id, 0)

    def get_node(self, node_id):
        for node in self.nodes:
            if node["id"] == node_id:
                return node
        return None

    def get_nodes(self):
        return self.nodes

    def get_connections(self):
        return self.connections
