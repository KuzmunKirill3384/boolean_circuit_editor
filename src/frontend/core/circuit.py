
class Circuit:
    def __init__(self):
        self.nodes = [] 
        self.connections = []
        self._next_node_id = 0 

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
        self.connections = [c for c in self.connections if c[0] != node_id and c[1] != node_id]

    def set_node_position(self, node_id, x, y):
        for node in self.nodes:
            if node["id"] == node_id:
                node["x"] = float(x)
                node["y"] = float(y)
                return True
        return False

    def connect_nodes(self, out_node_id, in_node_id):
        if out_node_id == in_node_id:
            return False
        if not any(n["id"] == out_node_id for n in self.nodes):
            return False
        if not any(n["id"] == in_node_id for n in self.nodes):
            return False
        if (out_node_id, in_node_id) in self.connections:
            return False
        self.connections.append((out_node_id, in_node_id))
        return True

    def disconnect_nodes(self, out_node_id, in_node_id):
        self.connections = [c for c in self.connections if c != (out_node_id, in_node_id)]

    def get_node(self, node_id):
        for node in self.nodes:
            if node["id"] == node_id:
                return node
        return None

    def get_nodes(self):
        return self.nodes

    def get_connections(self):
        return self.connections
