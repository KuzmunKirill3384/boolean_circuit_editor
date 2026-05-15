"""
Integration tests для проверки взаимодействия основных подсистем
редактора булевых схем.

Тестируются пользовательские сценарии:
- создание и вычисление схем;
- undo/redo операций;
- сохранение и загрузка XML;
- проверка корректности truth table;
- упрощение схем;
- сохранение структуры после сериализации;
- обработка ошибочных XML-файлов.

Тесты проверяют совместную работу нескольких модулей приложения одновременно
"""
import pytest

from backend.model.circuit import Circuit
from backend.commands.factory import CommandFactory
from backend.commands.history import CommandHistory

from backend.logic.truth_table import (
    get_truth_table,
    evaluate_circuit,
    simplify,
)

from backend.io.xml_builder import (
    export_to_xml,
    import_from_xml,
)


class TestIntegrationWorkflow:

    def test_full_workflow_save_load_truth_table(self, tmp_path):
        """Создание схемы -> вычисление -> XML save/load."""

        c = Circuit()

        in0 = c.add_node("IN", 0, 0)
        in1 = c.add_node("IN", 0, 100)
        and1 = c.add_node("AND", 200, 50)
        out1 = c.add_node("OUT", 400, 50)

        c.connect_pins(in0, 0, and1, 0)
        c.connect_pins(in1, 0, and1, 1)
        c.connect_pins(and1, 0, out1, 0)

        table_before = get_truth_table(c)

        assert len(table_before["rows"]) == 4

        result = evaluate_circuit(c, {
            in0: True,
            in1: True,
        })

        assert result[out1] == 1

        xml_path = tmp_path / "workflow.xml"

        export_to_xml(c, str(xml_path))

        loaded = import_from_xml(str(xml_path))

        valid, _ = loaded.validate_structure()
        assert valid

        table_after = get_truth_table(loaded)

        assert table_before == table_after

    def test_command_history_workflow(self):
        """Полный workflow undo/redo."""

        c = Circuit()
        history = CommandHistory()
        factory = CommandFactory(c)

        in0 = c.add_node("IN", 0, 0)
        out1 = c.add_node("OUT", 100, 0)

        connect_cmd = factory.create_connect_pins(in0, 0, out1, 0)

        history.execute(connect_cmd)

        assert len(c.connections) == 1

        history.undo()

        assert len(c.connections) == 0

        history.redo()

        assert len(c.connections) == 1

    def test_multiple_command_chain(self):
        """Цепочка execute/undo/redo команд."""

        c = Circuit()
        history = CommandHistory()
        factory = CommandFactory(c)

        in0 = c.add_node("IN", 0, 0)
        in1 = c.add_node("IN", 0, 100)
        and1 = c.add_node("AND", 200, 50)
        out1 = c.add_node("OUT", 400, 50)

        cmd1 = factory.create_connect_pins(in0, 0, and1, 0)
        cmd2 = factory.create_connect_pins(in1, 0, and1, 1)
        cmd3 = factory.create_connect_pins(and1, 0, out1, 0)

        history.execute(cmd1)
        history.execute(cmd2)
        history.execute(cmd3)

        assert len(c.connections) == 3

        history.undo()
        history.undo()
        history.undo()

        assert len(c.connections) == 0

        history.redo()
        history.redo()
        history.redo()

        assert len(c.connections) == 3

    def test_xml_roundtrip_preserves_structure(self, tmp_path):
        """XML roundtrip сохраняет структуру схемы."""

        c = Circuit()

        in0 = c.add_node("IN", 0, 0)
        xor1 = c.add_node("XOR", 200, 0)
        out1 = c.add_node("OUT", 400, 0)

        c.connect_pins(in0, 0, xor1, 0)
        c.connect_pins(xor1, 0, out1, 0)

        xml_path = tmp_path / "roundtrip.xml"

        export_to_xml(c, str(xml_path))

        loaded = import_from_xml(str(xml_path))

        assert len(loaded.get_nodes()) == len(c.get_nodes())
        assert len(loaded.connections) == len(c.connections)

        valid, _ = loaded.validate_structure()
        assert valid

    def test_invalid_xml_raises_exception(self, tmp_path):
        """Повреждённый XML вызывает исключение."""

        xml_path = tmp_path / "broken.xml"
        xml_path.write_text("<broken xml")

        with pytest.raises(Exception):
            import_from_xml(str(xml_path))

    def test_simplify_preserves_logic(self):
        """Упрощение схемы сохраняет корректную логику."""

        c = Circuit()

        in0 = c.add_node("IN", 0, 0)
        in1 = c.add_node("IN", 0, 100)
        and1 = c.add_node("AND", 200, 50)
        out1 = c.add_node("OUT", 400, 50)

        c.connect_pins(in0, 0, and1, 0)
        c.connect_pins(in1, 0, and1, 1)
        c.connect_pins(and1, 0, out1, 0)

        simplified = simplify(c, {in0: True})

        result = evaluate_circuit(simplified, {in1: True})

        assert result[out1] == 1 

    def test_large_circuit_evaluation(self):
        """Вычисление большой схемы."""

        c = Circuit()

        inputs = [c.add_node("IN", i*50, 0) for i in range(10)]

        prev = inputs[0]
        for i in range(1, 10):
            gate = c.add_node("AND", i*100, 50)
            c.connect_pins(prev, 0, gate, 0)
            c.connect_pins(inputs[i], 0, gate, 1)
            prev = gate

        out1 = c.add_node("OUT", 1100, 50)
        c.connect_pins(prev, 0, out1, 0)

        values = {node_id: True for node_id in inputs}

        result = evaluate_circuit(c, values)

        assert result[out1] == 1

    def test_loaded_circuit_matches_original_logic(self, tmp_path):
        """Загруженная схема даёт тот же результат."""

        c = Circuit()

        in0 = c.add_node("IN", 0, 0)
        in1 = c.add_node("IN", 0, 100)
        xor1 = c.add_node("XOR", 200, 50)
        out1 = c.add_node("OUT", 400, 50)

        c.connect_pins(in0, 0, xor1, 0)
        c.connect_pins(in1, 0, xor1, 1)
        c.connect_pins(xor1, 0, out1, 0)

        original = evaluate_circuit(c, {in0: True, in1: False})

        xml_path = tmp_path / "logic.xml"
        export_to_xml(c, str(xml_path))

        loaded = import_from_xml(str(xml_path))

        result = evaluate_circuit(loaded, {in0: True, in1: False})

        assert list(result.values())[0] == list(original.values())[0]

    def test_truth_table_consistency_after_xml_roundtrip(self, tmp_path):
        """Truth table совпадает после XML roundtrip."""

        c = Circuit()

        in0 = c.add_node("IN", 0, 0)
        in1 = c.add_node("IN", 0, 100)
        or1 = c.add_node("OR", 200, 50)
        out1 = c.add_node("OUT", 400, 50)

        c.connect_pins(in0, 0, or1, 0)
        c.connect_pins(in1, 0, or1, 1)
        c.connect_pins(or1, 0, out1, 0)

        before = get_truth_table(c)

        xml_path = tmp_path / "truth_table.xml"
        export_to_xml(c, str(xml_path))

        loaded = import_from_xml(str(xml_path))

        after = get_truth_table(loaded)

        assert before == after

    def test_redo_stack_cleared_after_new_command(self):
        """Redo stack очищается после новой команды."""

        c = Circuit()
        history = CommandHistory()
        factory = CommandFactory(c)

        in0 = c.add_node("IN", 0, 0)
        out1 = c.add_node("OUT", 100, 0)

        cmd1 = factory.create_connect_pins(in0, 0, out1, 0)

        history.execute(cmd1)
        history.undo()

        assert len(c.connections) == 0

        out2 = c.add_node("OUT", 200, 0)
        cmd2 = factory.create_connect_pins(in0, 0, out2, 0)

        history.execute(cmd2)

        history.redo()
        assert len(c.connections) == 1

    def test_complex_circuit_workflow(self, tmp_path):
        """Сложный пользовательский сценарий."""

        c = Circuit()

        in0 = c.add_node("IN", 0, 0)
        in1 = c.add_node("IN", 0, 100)
        in2 = c.add_node("IN", 0, 200)

        and1 = c.add_node("AND", 200, 50)
        xor1 = c.add_node("XOR", 400, 100)
        or1 = c.add_node("OR", 600, 100)
        out1 = c.add_node("OUT", 800, 100)

        c.connect_pins(in0, 0, and1, 0)
        c.connect_pins(in1, 0, and1, 1)
        c.connect_pins(and1, 0, xor1, 0)
        c.connect_pins(in2, 0, xor1, 1)
        c.connect_pins(xor1, 0, or1, 0)
        c.connect_pins(in0, 0, or1, 1)
        c.connect_pins(or1, 0, out1, 0)

        valid, _ = c.validate_structure()
        assert valid

        result_before = evaluate_circuit(c, {
            in0: True,
            in1: True,
            in2: False,
        })

        xml_path = tmp_path / "complex.xml"
        export_to_xml(c, str(xml_path))

        loaded = import_from_xml(str(xml_path))

        result_after = evaluate_circuit(loaded, {
            in0: True,
            in1: True,
            in2: False,
        })

        assert list(result_before.values())[0] == list(result_after.values())[0]

        valid, _ = loaded.validate_structure()
        assert valid