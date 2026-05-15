from backend.model.circuit import Circuit
from backend.model.elements import AndNode, InputNode, create_node
from backend.model.node import CircuitNode


def test_circuit_is_composite_container():
    c = Circuit()
    assert hasattr(c, "accept")
    assert hasattr(c, "iter_components")


def test_create_node_returns_typed_leaf():
    data = {"id": 1, "type": "AND", "x": 0.0, "y": 0.0}
    node = create_node(data)
    assert isinstance(node, AndNode)
    assert node.node_id == 1
    assert node.to_dict()["type"] == "AND"


def test_input_node_type():
    node = create_node({"id": 0, "type": "in", "x": 1.0, "y": 2.0})
    assert isinstance(node, InputNode)
    assert node.node_type == "IN"


def test_get_nodes_returns_dict_snapshots():
    c = Circuit()
    c.add_node("OR", 3, 4)
    nodes = c.get_nodes()
    nodes[0]["type"] = "IN"
    assert c.get_node(nodes[0]["id"])["type"] == "OR"
