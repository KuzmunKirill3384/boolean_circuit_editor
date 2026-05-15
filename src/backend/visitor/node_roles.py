from __future__ import annotations

from backend.model.elements import (
    AndNode,
    Const0Node,
    Const1Node,
    EqualNode,
    InputNode,
    OrNode,
    OutputNode,
    XorNode,
)
from backend.visitor.visitor import CircuitVisitor


class NodeRolesVisitor(CircuitVisitor):
    """Собирает id входов и выходов схемы при обходе."""

    def __init__(self) -> None:
        self.input_ids: list[int] = []
        self.output_ids: list[int] = []

    def visit_input(self, node: InputNode) -> None:
        self.input_ids.append(node.node_id)

    def visit_output(self, node: OutputNode) -> None:
        self.output_ids.append(node.node_id)

    def visit_and(self, node: AndNode) -> None:
        pass

    def visit_or(self, node: OrNode) -> None:
        pass

    def visit_xor(self, node: XorNode) -> None:
        pass

    def visit_equal(self, node: EqualNode) -> None:
        pass

    def visit_const_0(self, node: Const0Node) -> None:
        pass

    def visit_const_1(self, node: Const1Node) -> None:
        pass
