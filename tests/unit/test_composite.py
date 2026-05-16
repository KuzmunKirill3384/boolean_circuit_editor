"""
Тесты для Composite + Factory паттернов в модели схемы.

Проверяется:
  - Circuit как композитный контейнер (методы accept, iter_components)
  - Корректное создание типизированных узлов через create_node()
  - Правильная работа Snapshot'ов (get_nodes возвращает копии)
"""

from backend.model.circuit import Circuit
from backend.model.elements import AndNode, InputNode, create_node
from backend.model.node import CircuitNode


def test_circuit_is_composite_container():
    """Проверяет, что Circuit реализует интерфейс композитного объекта 
    (методы accept и iter_components)."""
    c = Circuit()
    assert hasattr(c, "accept")
    assert hasattr(c, "iter_components")


def test_create_node_returns_typed_leaf():
    """Проверяет, что фабрика create_node() возвращает объект 
    конкретного класса в зависимости от типа узла (AndNode и т.д.)."""
    data = {"id": 1, "type": "AND", "x": 0.0, "y": 0.0}
    node = create_node(data)
    assert isinstance(node, AndNode)
    assert node.node_id == 1
    assert node.to_dict()["type"] == "AND"


def test_input_node_type():
    """Проверяет корректное создание и нормализацию типа для InputNode."""
    node = create_node({"id": 0, "type": "in", "x": 1.0, "y": 2.0})
    assert isinstance(node, InputNode)
    assert node.node_type == "IN"


def test_get_nodes_returns_dict_snapshots():
    """Проверяет, что get_nodes() возвращает снимки (копии) данных,
    изменение которых не влияет на внутреннее состояние Circuit."""
    c = Circuit()
    c.add_node("OR", 3, 4)
    nodes = c.get_nodes()
    nodes[0]["type"] = "IN"
    assert c.get_node(nodes[0]["id"])["type"] == "OR"
