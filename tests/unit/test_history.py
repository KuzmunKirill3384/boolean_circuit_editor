"""
Тесты для модуля backend.commands.history.

Проверяется выполнение и отмена каждой команды:
  - AddNodeCommand
  - RemoveNodeCommand
  - MoveNodeCommand
  - ConnectPinsCommand
  - DisconnectPinsCommand

А также логика стека undo/redo в CommandHistory.
"""

import pytest
from backend.model.circuit import Circuit
from backend.commands.history import (
    CommandHistory,
    AddNodeCommand,
    RemoveNodeCommand,
    MoveNodeCommand,
    ConnectPinsCommand,
    DisconnectPinsCommand,
)


# Вспомогательная функция

def _make_connected_circuit():
    """IN -> AND(pin0), IN -> AND(pin1), AND -> OUT. Возвращает circuit и id узлов."""
    c = Circuit()
    in0 = c.add_node("IN", 0, 0)
    in1 = c.add_node("IN", 0, 50)
    and1 = c.add_node("AND", 100, 25)
    out1 = c.add_node("OUT", 200, 25)
    c.connect_pins(in0, 0, and1, 0)
    c.connect_pins(in1, 0, and1, 1)
    c.connect_pins(and1, 0, out1, 0)
    return c, in0, in1, and1, out1


# AddNodeCommand

class TestAddNodeCommand:

    def test_execute_adds_node(self):
        """После execute узел с нужным типом появляется в схеме."""
        c = Circuit()
        h = CommandHistory()
        cmd = AddNodeCommand(c, "AND", 10, 20)
        h.execute(cmd)

        assert cmd.node_id is not None
        node = c.get_node(cmd.node_id)
        assert node is not None
        assert node["type"] == "AND"
        assert node["x"] == pytest.approx(10)
        assert node["y"] == pytest.approx(20)

    def test_undo_removes_node(self):
        """После undo узел исчезает из схемы."""
        c = Circuit()
        h = CommandHistory()
        cmd = AddNodeCommand(c, "OR", 0, 0)
        h.execute(cmd)
        nid = cmd.node_id
        h.undo()

        assert c.get_node(nid) is None

    def test_redo_restores_node(self):
        """После redo узел снова появляется.

        Примечание: redo вызывает execute() повторно, поэтому cmd.node_id
        обновляется на новый идентификатор (счётчик id не откатывается при undo).
        Проверяем именно актуальный cmd.node_id после redo.
        """
        c = Circuit()
        h = CommandHistory()
        cmd = AddNodeCommand(c, "XOR", 5, 5)
        h.execute(cmd)
        h.undo()
        h.redo()

        # cmd.node_id обновлён execute() при redo
        assert c.get_node(cmd.node_id) is not None


# RemoveNodeCommand

class TestRemoveNodeCommand:

    def test_execute_removes_node(self):
        """После execute узел исчезает."""
        c = Circuit()
        nid = c.add_node("IN", 0, 0)
        h = CommandHistory()
        h.execute(RemoveNodeCommand(c, nid))

        assert c.get_node(nid) is None

    def test_undo_restores_node(self):
        """После undo узел возвращается с тем же типом."""
        c = Circuit()
        nid = c.add_node("IN", 30, 40)
        h = CommandHistory()
        h.execute(RemoveNodeCommand(c, nid))
        h.undo()

        node = c.get_node(nid)
        assert node is not None
        assert node["type"] == "IN"

    def test_execute_removes_attached_connections(self):
        """При удалении узла его связи тоже удаляются."""
        c, in0, in1, and1, out1 = _make_connected_circuit()
        h = CommandHistory()
        h.execute(RemoveNodeCommand(c, and1))

        # Связей с and1 быть не должно
        conns = c.get_connections()
        assert all(and1 not in (c[0], c[2]) for c in conns)

    def test_undo_restores_connections(self):
        """После undo связи удалённого узла восстанавливаются."""
        c, in0, in1, and1, out1 = _make_connected_circuit()
        original_conns = set(c.get_connections())
        h = CommandHistory()
        h.execute(RemoveNodeCommand(c, and1))
        h.undo()

        assert set(c.get_connections()) == original_conns


# MoveNodeCommand

class TestMoveNodeCommand:

    def test_execute_moves_node(self):
        """После execute узел находится на новых координатах."""
        c = Circuit()
        nid = c.add_node("AND", 10, 20)
        h = CommandHistory()
        h.execute(MoveNodeCommand(c, nid, 10, 20, 100, 200))

        node = c.get_node(nid)
        assert node["x"] == pytest.approx(100)
        assert node["y"] == pytest.approx(200)

    def test_undo_restores_position(self):
        """После undo узел возвращается на старые координаты."""
        c = Circuit()
        nid = c.add_node("OR", 10, 20)
        h = CommandHistory()
        h.execute(MoveNodeCommand(c, nid, 10, 20, 999, 999))
        h.undo()

        node = c.get_node(nid)
        assert node["x"] == pytest.approx(10)
        assert node["y"] == pytest.approx(20)

    def test_redo_moves_again(self):
        """После redo узел снова оказывается на новых координатах."""
        c = Circuit()
        nid = c.add_node("XOR", 0, 0)
        h = CommandHistory()
        h.execute(MoveNodeCommand(c, nid, 0, 0, 50, 60))
        h.undo()
        h.redo()

        node = c.get_node(nid)
        assert node["x"] == pytest.approx(50)
        assert node["y"] == pytest.approx(60)

    def test_float_coordinates_preserved(self):
        """Дробные координаты сохраняются без потерь."""
        c = Circuit()
        nid = c.add_node("IN", 0, 0)
        h = CommandHistory()
        h.execute(MoveNodeCommand(c, nid, 0, 0, 12.5, 37.75))

        node = c.get_node(nid)
        assert node["x"] == pytest.approx(12.5)
        assert node["y"] == pytest.approx(37.75)


# ConnectPinsCommand

class TestConnectPinsCommand:

    def test_execute_creates_connection(self):
        """После execute связь между пинами существует."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        and1 = c.add_node("AND", 100, 0)
        h = CommandHistory()
        h.execute(ConnectPinsCommand(c, in0, 0, and1, 0))

        assert (in0, 0, and1, 0) in c.get_connections()

    def test_undo_removes_connection(self):
        """После undo связь исчезает."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        and1 = c.add_node("AND", 100, 0)
        h = CommandHistory()
        h.execute(ConnectPinsCommand(c, in0, 0, and1, 0))
        h.undo()

        assert (in0, 0, and1, 0) not in c.get_connections()

    def test_redo_recreates_connection(self):
        """После redo связь появляется снова."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        and1 = c.add_node("AND", 100, 0)
        h = CommandHistory()
        h.execute(ConnectPinsCommand(c, in0, 0, and1, 0))
        h.undo()
        h.redo()

        assert (in0, 0, and1, 0) in c.get_connections()

    def test_execute_multiple_pins(self):
        """Можно подключить оба входных пина AND."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        in1 = c.add_node("IN", 0, 50)
        and1 = c.add_node("AND", 100, 25)
        h = CommandHistory()
        h.execute(ConnectPinsCommand(c, in0, 0, and1, 0))
        h.execute(ConnectPinsCommand(c, in1, 0, and1, 1))

        conns = c.get_connections()
        assert (in0, 0, and1, 0) in conns
        assert (in1, 0, and1, 1) in conns


# DisconnectPinsCommand

class TestDisconnectPinsCommand:

    def test_execute_removes_connection(self):
        """После execute связь исчезает."""
        c, in0, in1, and1, out1 = _make_connected_circuit()
        h = CommandHistory()
        h.execute(DisconnectPinsCommand(c, in0, 0, and1, 0))

        assert (in0, 0, and1, 0) not in c.get_connections()

    def test_undo_restores_connection(self):
        """После undo связь восстанавливается."""
        c, in0, in1, and1, out1 = _make_connected_circuit()
        h = CommandHistory()
        h.execute(DisconnectPinsCommand(c, in0, 0, and1, 0))
        h.undo()

        assert (in0, 0, and1, 0) in c.get_connections()

    def test_redo_disconnects_again(self):
        """После redo связь снова удаляется."""
        c, in0, in1, and1, out1 = _make_connected_circuit()
        h = CommandHistory()
        h.execute(DisconnectPinsCommand(c, in0, 0, and1, 0))
        h.undo()
        h.redo()

        assert (in0, 0, and1, 0) not in c.get_connections()


# CommandHistory — логика стека

class TestCommandHistory:

    def test_undo_redo_stack(self):
        """Последовательный undo/redo корректно управляет количеством узлов."""
        c = Circuit()
        h = CommandHistory()
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

    def test_new_command_clears_redo_stack(self):
        """Выполнение новой команды после undo очищает redo-стек."""
        c = Circuit()
        h = CommandHistory()
        h.execute(AddNodeCommand(c, "IN", 0, 0))
        h.undo()
        # Теперь выполняем новую команду — redo-стек должен очиститься
        h.execute(AddNodeCommand(c, "OR", 10, 10))
        assert h.redo() is False  # ничего нет в redo

    def test_undo_empty_stack_returns_false(self):
        """Undo на пустом стеке возвращает False и не падает."""
        h = CommandHistory()
        assert h.undo() is False

    def test_redo_empty_stack_returns_false(self):
        """Redo на пустом стеке возвращает False и не падает."""
        h = CommandHistory()
        assert h.redo() is False

    def test_clear_empties_both_stacks(self):
        """После clear() и undo, и redo стеки пусты."""
        c = Circuit()
        h = CommandHistory()
        h.execute(AddNodeCommand(c, "AND", 0, 0))
        h.clear()
        assert h.undo() is False
        assert h.redo() is False

    def test_multiple_undos_then_single_redo(self):
        """После нескольких undo один redo восстанавливает только одну команду."""
        c = Circuit()
        h = CommandHistory()
        cmd1 = AddNodeCommand(c, "IN", 0, 0)
        cmd2 = AddNodeCommand(c, "OUT", 10, 0)
        cmd3 = AddNodeCommand(c, "AND", 20, 0)
        h.execute(cmd1)
        h.execute(cmd2)
        h.execute(cmd3)

        h.undo()
        h.undo()
        assert len(c.get_nodes()) == 1
        h.redo()
        assert len(c.get_nodes()) == 2
