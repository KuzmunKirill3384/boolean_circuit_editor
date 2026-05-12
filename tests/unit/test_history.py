import pytest
from backend.model.circuit import Circuit
from backend.commands.history import (
    CommandHistory,
    AddNodeCommand,
    RemoveNodeCommand,
)


def test_add_node_command():
    """Команда добавления узла выполняется и отменяется."""
    c = Circuit()
    h = CommandHistory()
    cmd = AddNodeCommand(c, "AND", 10, 20)
    h.execute(cmd)
    # Узел должен появиться
    assert cmd.node_id is not None
    assert c.get_node(cmd.node_id) is not None
    # Отменяем
    h.undo()
    assert c.get_node(cmd.node_id) is None


def test_remove_node_command():
    """Команда удаления узла выполняется и отменяется (узел восстанавливается)."""
    c = Circuit()
    nid = c.add_node("IN", 0, 0)
    cmd = RemoveNodeCommand(c, nid)
    h = CommandHistory()
    h.execute(cmd)
    # Узел должен исчезнуть
    assert c.get_node(nid) is None
    # Отменяем — узел возвращается
    h.undo()
    assert c.get_node(nid) is not None


def test_undo_redo_stack():
    """Последовательность undo/redo изменяет количество узлов корректно."""
    c = Circuit()
    h = CommandHistory()
    # Добавляем два узла
    cmd1 = AddNodeCommand(c, "IN", 0, 0)
    cmd2 = AddNodeCommand(c, "OUT", 50, 50)
    h.execute(cmd1)
    h.execute(cmd2)
    assert len(c.get_nodes()) == 2

    h.undo()
    assert len(c.get_nodes()) == 1
    h.undo()
    assert len(c.get_nodes()) == 0

    h.redo()
    assert len(c.get_nodes()) == 1
    h.redo()
    assert len(c.get_nodes()) == 2