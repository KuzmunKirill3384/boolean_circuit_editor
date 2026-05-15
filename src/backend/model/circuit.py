from __future__ import annotations

from typing import TYPE_CHECKING, Any

from backend.model.elements import create_node
from backend.model.node import CircuitNode

if TYPE_CHECKING:
    from backend.visitor.visitor import CircuitVisitor


class Circuit:
    """Контейнер схемы (Composite): узлы и связи между пинами."""

    ALLOWED_NODE_TYPES = {"AND", "OR", "XOR", "EQUAL", "IN", "OUT", "CONST_0", "CONST_1"}

    def __init__(self):
        self._nodes: list[CircuitNode] = []
        self.connections: list[tuple[int, int, int, int]] = []
        self._next_node_id = 0

    @staticmethod
    def get_pin_counts(node_type):
        pin_counts = {
            "AND": (2, 1),
            "OR": (2, 1),
            "XOR": (2, 1),
            "EQUAL": (2, 1),
            "IN": (0, 1),
            "OUT": (1, 0),
            "CONST_0": (0, 1),
            "CONST_1": (0, 1),
        }
        return pin_counts.get(node_type.upper(), (1, 1))

    @classmethod
    def is_supported_node_type(cls, node_type):
        return (node_type or "").upper() in cls.ALLOWED_NODE_TYPES

    @property
    def nodes(self) -> list[dict[str, Any]]:
        """Совместимость: список узлов как dict (для XML и legacy-кода)."""
        return [n.to_dict() for n in self._nodes]

    @nodes.setter
    def nodes(self, value: list[dict[str, Any]]) -> None:
        self._nodes = [create_node(n) for n in value]

    def accept(self, visitor: CircuitVisitor) -> None:
        visitor.visit_circuit(self)

    def iter_components(self) -> list[CircuitNode]:
        return list(self._nodes)

    def get_component(self, node_id: int) -> CircuitNode | None:
        for node in self._nodes:
            if node.node_id == node_id:
                return node
        return None

    def add_node(self, node_type, x, y):
        if not self.is_supported_node_type(node_type):
            raise ValueError(f"Unsupported node type: {node_type}")
        node = create_node(
            {
                "id": self._next_node_id,
                "type": node_type.upper(),
                "x": float(x),
                "y": float(y),
            }
        )
        self._nodes.append(node)
        self._next_node_id += 1
        return node.node_id

    def add_node_with_id(self, node):
        if not self.is_supported_node_type(node.get("type")):
            raise ValueError(f"Unsupported node type: {node.get('type')}")
        component = create_node(node)
        self._nodes.append(component)
        self._next_node_id = max(self._next_node_id, component.node_id + 1)

    def remove_node(self, node_id):
        self._nodes = [n for n in self._nodes if n.node_id != node_id]
        self.connections = [c for c in self.connections if c[0] != node_id and c[2] != node_id]

    def set_node_position(self, node_id, x, y):
        for node in self._nodes:
            if node.node_id == node_id:
                data = node.to_dict()
                data["x"] = float(x)
                data["y"] = float(y)
                idx = self._nodes.index(node)
                self._nodes[idx] = create_node(data)
                return True
        return False

    def set_node_type(self, node_id: int, node_type: str) -> bool:
        if not self.is_supported_node_type(node_type):
            raise ValueError(f"Unsupported node type: {node_type}")
        for i, node in enumerate(self._nodes):
            if node.node_id == node_id:
                data = node.to_dict()
                data["type"] = node_type.upper()
                self._nodes[i] = create_node(data)
                return True
        return False

    def validate_connection(self, out_node_id, out_pin, in_node_id, in_pin):
        if out_pin < 0 or in_pin < 0:
            return False, "Pin index must be non-negative"

        if out_node_id == in_node_id:
            return False, "Cannot connect node to itself"

        out_node = self.get_node(out_node_id)
        in_node = self.get_node(in_node_id)
        if not out_node or not in_node:
            return False, "Node not found"

        _, out_output_pins = self.get_pin_counts(out_node["type"])
        in_input_pins, _ = self.get_pin_counts(in_node["type"])

        if out_pin >= out_output_pins:
            return False, f"Output pin {out_pin} does not exist on {out_node['type']}"
        if in_pin >= in_input_pins:
            return False, f"Input pin {in_pin} does not exist on {in_node['type']}"

        for conn in self.connections:
            if conn[2] == in_node_id and conn[3] == in_pin:
                return False, f"Input pin {in_pin} is already connected"

        if self.would_create_cycle(out_node_id, in_node_id):
            return False, "Connection would create a cycle"

        return True, ""

    def would_create_cycle(self, start_id, end_id):
        visited = set()

        def dfs(node_id):
            if node_id in visited:
                return False
            visited.add(node_id)
            for conn in self.connections:
                if conn[0] == node_id:
                    if conn[2] == start_id:
                        return True
                    if dfs(conn[2]):
                        return True
            return False

        return dfs(end_id)

    def has_cycle(self):
        graph = {}
        for node in self._nodes:
            graph[node.node_id] = []
        for out_id, _out_pin, in_id, _in_pin in self.connections:
            graph.setdefault(out_id, []).append(in_id)
            graph.setdefault(in_id, [])

        visiting = set()
        visited = set()

        def dfs(node_id):
            if node_id in visited:
                return False
            if node_id in visiting:
                return True
            visiting.add(node_id)
            for nxt in graph.get(node_id, []):
                if dfs(nxt):
                    return True
            visiting.remove(node_id)
            visited.add(node_id)
            return False

        return any(dfs(node_id) for node_id in graph)

    def validate_structure(self):
        node_map = {node.node_id: node.to_dict() for node in self._nodes}
        used_input_pins = {}

        for out_id, out_pin, in_id, in_pin in self.connections:
            out_node = node_map.get(out_id)
            in_node = node_map.get(in_id)
            if out_node is None or in_node is None:
                return False, "Connection references a missing node"

            in_count, _ = self.get_pin_counts(in_node["type"])
            _, out_count = self.get_pin_counts(out_node["type"])
            if in_pin < 0 or in_pin >= in_count:
                return False, f"Invalid input pin {in_pin} for node {in_id}"
            if out_pin < 0 or out_pin >= out_count:
                return False, f"Invalid output pin {out_pin} for node {out_id}"

            key_in = (in_id, in_pin)
            if key_in in used_input_pins:
                return False, f"Input pin {in_pin} of node {in_id} has multiple sources"
            used_input_pins[key_in] = True

        if self.has_cycle():
            return False, "Circuit must be acyclic"

        return True, ""

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

    def get_node(self, node_id):
        component = self.get_component(node_id)
        return component.to_dict() if component else None

    def get_nodes(self):
        return [n.to_dict() for n in self._nodes]

    def get_connections(self):
        return self.connections

    def clear(self) -> None:
        self._nodes = []
        self.connections = []
        self._next_node_id = 0
