"""
Тесты для модуля backend.commands.factory (CommandFactory).

Проверяется:
  - Создание команд правильного типа (AddNodeCommand, RemoveNodeCommand и др.)
  - Валидация параметров при создании команд
  - Обработка ошибочных ситуаций (неподдерживаемый тип узла, несуществующий узел, создание цикла)
"""

import pytest

from backend.model.circuit import Circuit
from backend.commands.factory import CommandFactory, CommandFactoryError
from backend.commands.history import (
    AddNodeCommand,
    ConnectPinsCommand,
    RemoveNodeCommand,
)


def test_factory_creates_expected_command_types():
    """Проверяет, что CommandFactory создаёт команды правильных типов 
    (AddNodeCommand, RemoveNodeCommand, ConnectPinsCommand)."""
    circuit = Circuit()
    factory = CommandFactory(circuit)

    add_cmd = factory.create_add_node("AND", 10, 20)
    assert isinstance(add_cmd, AddNodeCommand)

    node_id = circuit.add_node("IN", 0, 0)
    gate_id = circuit.add_node("OUT", 50, 50)
    circuit.connect_pins(node_id, 0, gate_id, 0)

    remove_cmd = factory.create_remove_node(gate_id)
    assert isinstance(remove_cmd, RemoveNodeCommand)

    circuit2 = Circuit()
    f2 = CommandFactory(circuit2)
    n1 = circuit2.add_node("IN", 0, 0)
    n2 = circuit2.add_node("AND", 10, 0)
    connect_cmd = f2.create_connect_pins(n1, 0, n2, 0)
    assert isinstance(connect_cmd, ConnectPinsCommand)


def test_factory_rejects_invalid_arguments():
    """Проверяет валидацию параметров при создании команд:
    - неподдерживаемый тип узла
    - попытка удалить несуществующий узел
    - попытка создать цикл"""
    circuit = Circuit()
    factory = CommandFactory(circuit)

    with pytest.raises(CommandFactoryError, match="Unsupported"):
        factory.create_add_node("NAND", 0, 0)

    with pytest.raises(CommandFactoryError, match="not found"):
        factory.create_remove_node(999)

    a1 = circuit.add_node("AND", 0, 0)
    a2 = circuit.add_node("AND", 10, 0)
    circuit.connect_pins(a1, 0, a2, 0)
    with pytest.raises(CommandFactoryError, match="cycle"):
        factory.create_connect_pins(a2, 0, a1, 0)
