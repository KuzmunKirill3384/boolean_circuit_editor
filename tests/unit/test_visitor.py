from backend.model.circuit import Circuit
from backend.model.elements import AndNode, InputNode, OutputNode
from backend.visitor.node_roles import NodeRolesVisitor
from backend.visitor.visitor import CircuitVisitor


class _TypeCaptureVisitor(CircuitVisitor):
    def __init__(self):
        self.types: list[str] = []

    def visit_input(self, node: InputNode) -> None:
        self.types.append("IN")

    def visit_output(self, node: OutputNode) -> None:
        self.types.append("OUT")

    def visit_and(self, node: AndNode) -> None:
        self.types.append("AND")

    def visit_or(self, node) -> None:
        self.types.append("OR")

    def visit_xor(self, node) -> None:
        self.types.append("XOR")

    def visit_equal(self, node) -> None:
        self.types.append("EQUAL")

    def visit_const_0(self, node) -> None:
        self.types.append("CONST_0")

    def visit_const_1(self, node) -> None:
        self.types.append("CONST_1")


def test_accept_dispatches_by_node_type():
    c = Circuit()
    c.add_node("IN", 0, 0)
    c.add_node("AND", 10, 0)
    c.add_node("OUT", 20, 0)

    visitor = _TypeCaptureVisitor()
    c.accept(visitor)
    assert visitor.types == ["IN", "AND", "OUT"]


def test_node_roles_visitor_collects_io():
    c = Circuit()
    in_id = c.add_node("IN", 0, 0)
    out_id = c.add_node("OUT", 10, 0)
    c.add_node("AND", 5, 0)

    roles = NodeRolesVisitor()
    c.accept(roles)
    assert roles.input_ids == [in_id]
    assert roles.output_ids == [out_id]


def test_component_accept_on_single_node():
    c = Circuit()
    node_id = c.add_node("XOR", 0, 0)
    component = c.get_component(node_id)
    assert component is not None

    visitor = _TypeCaptureVisitor()
    component.accept(visitor)
    assert visitor.types == ["XOR"]
