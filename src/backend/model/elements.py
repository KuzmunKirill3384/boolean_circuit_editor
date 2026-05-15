from __future__ import annotations

from typing import Any

from backend.model.node import CircuitNode


class InputNode(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_input(self)


class OutputNode(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_output(self)


class AndNode(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_and(self)


class OrNode(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_or(self)


class XorNode(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_xor(self)


class EqualNode(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_equal(self)


class Const0Node(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_const_0(self)


class Const1Node(CircuitNode):
    def accept(self, visitor) -> None:
        visitor.visit_const_1(self)


_NODE_CLASS_BY_TYPE: dict[str, type[CircuitNode]] = {
    "IN": InputNode,
    "OUT": OutputNode,
    "AND": AndNode,
    "OR": OrNode,
    "XOR": XorNode,
    "EQUAL": EqualNode,
    "CONST_0": Const0Node,
    "CONST_1": Const1Node,
}


def create_node(data: dict[str, Any]) -> CircuitNode:
    node_type = str(data.get("type", "")).upper()
    cls = _NODE_CLASS_BY_TYPE.get(node_type, CircuitNode)
    return cls(data)
