from __future__ import annotations

from backend.model.circuit import Circuit
from backend.commands.history import (
    AddNodeCommand,
    ConnectPinsCommand,
    DisconnectPinsCommand,
    MoveNodeCommand,
    RemoveNodeCommand,
)


class CommandFactoryError(ValueError):
    """Ошибка валидации параметров при создании команды."""


class CommandFactory:
    """Фабрика команд редактирования (Factory)."""

    def __init__(self, circuit: Circuit):
        self._circuit = circuit

    def bind_circuit(self, circuit: Circuit) -> None:
        self._circuit = circuit

    def create_add_node(self, node_type: str, x: float, y: float) -> AddNodeCommand:
        if not Circuit.is_supported_node_type(node_type):
            raise CommandFactoryError(f"Unsupported node type: {node_type}")
        return AddNodeCommand(self._circuit, node_type, float(x), float(y))

    def create_remove_node(self, node_id: int) -> RemoveNodeCommand:
        if self._circuit.get_node(node_id) is None:
            raise CommandFactoryError(f"Node {node_id} not found")
        return RemoveNodeCommand(self._circuit, node_id)

    def create_move_node(
        self,
        node_id: int,
        old_x: float,
        old_y: float,
        new_x: float,
        new_y: float,
    ) -> MoveNodeCommand:
        if self._circuit.get_node(node_id) is None:
            raise CommandFactoryError(f"Node {node_id} not found")
        return MoveNodeCommand(
            self._circuit, node_id, float(old_x), float(old_y), float(new_x), float(new_y)
        )

    def create_connect_pins(
        self,
        out_node_id: int,
        out_pin: int,
        in_node_id: int,
        in_pin: int,
    ) -> ConnectPinsCommand:
        if out_pin < 0 or in_pin < 0:
            raise CommandFactoryError("Pin index must be non-negative")
        valid, message = self._circuit.validate_connection(
            out_node_id, out_pin, in_node_id, in_pin
        )
        if not valid:
            raise CommandFactoryError(message)
        return ConnectPinsCommand(
            self._circuit, out_node_id, out_pin, in_node_id, in_pin
        )

    def create_disconnect_pins(
        self,
        out_node_id: int,
        out_pin: int,
        in_node_id: int,
        in_pin: int,
    ) -> DisconnectPinsCommand:
        connection = (out_node_id, out_pin, in_node_id, in_pin)
        if connection not in self._circuit.get_connections():
            raise CommandFactoryError("Connection does not exist")
        return DisconnectPinsCommand(
            self._circuit, out_node_id, out_pin, in_node_id, in_pin
        )
