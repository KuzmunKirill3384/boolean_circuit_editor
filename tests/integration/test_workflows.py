"""
Интеграционные тесты для проверки взаимодействия основных подсистем
редактора булевых схем.

Тестируются пользовательские сценарии:
  - создание и вычисление схем;
  - undo/redo операций;
  - сохранение и загрузка XML;
  - проверка корректности truth table;
  - упрощение схем;
  - сохранение структуры после сериализации;
  - обработка ошибочных XML-файлов.

Тесты проверяют совместную работу нескольких модулей приложения одновременно.
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


# Вспомогательные функции

def _get_nodes_by_type(circuit, node_type):
    """Возвращает список id узлов заданного типа из схемы."""
    return sorted(n["id"] for n in circuit.get_nodes() if n["type"] == node_type)


def _and_circuit():
    """IN0, IN1 → AND → OUT. Возвращает (circuit, in0, in1, and1, out1)."""
    c = Circuit()
    in0  = c.add_node("IN",  0,   0)
    in1  = c.add_node("IN",  0, 100)
    and1 = c.add_node("AND", 200, 50)
    out1 = c.add_node("OUT", 400, 50)
    c.connect_pins(in0, 0, and1, 0)
    c.connect_pins(in1, 0, and1, 1)
    c.connect_pins(and1, 0, out1, 0)
    return c, in0, in1, and1, out1


def _xor_circuit():
    """IN0, IN1 → XOR → OUT. Возвращает (circuit, in0, in1, xor1, out1)."""
    c = Circuit()
    in0  = c.add_node("IN",  0,   0)
    in1  = c.add_node("IN",  0, 100)
    xor1 = c.add_node("XOR", 200, 50)
    out1 = c.add_node("OUT", 400, 50)
    c.connect_pins(in0, 0, xor1, 0)
    c.connect_pins(in1, 0, xor1, 1)
    c.connect_pins(xor1, 0, out1, 0)
    return c, in0, in1, xor1, out1


def _or_circuit():
    """IN0, IN1 → OR → OUT. Возвращает (circuit, in0, in1, or1, out1)."""
    c = Circuit()
    in0 = c.add_node("IN",  0,   0)
    in1 = c.add_node("IN",  0, 100)
    or1 = c.add_node("OR",  200, 50)
    out1 = c.add_node("OUT", 400, 50)
    c.connect_pins(in0, 0, or1, 0)
    c.connect_pins(in1, 0, or1, 1)
    c.connect_pins(or1, 0, out1, 0)
    return c, in0, in1, or1, out1


class TestIntegrationWorkflow:


    def test_full_workflow_save_load_truth_table(self, tmp_path):
        """Полный workflow: создание схемы, вычисление, сохранение и загрузка XML.

        Проверяет, что таблица истинности до и после XML-roundtrip совпадает.
        """
        c, in0, in1, and1, out1 = _and_circuit()

        table_before = get_truth_table(c)
        assert len(table_before["rows"]) == 4  # 2^2 строки

        # Вычисление: AND(1, 1) = 1
        assert evaluate_circuit(c, {in0: 1, in1: 1})[out1] == 1
        # Вычисление: AND(1, 0) = 0
        assert evaluate_circuit(c, {in0: 1, in1: 0})[out1] == 0

        xml_path = tmp_path / "workflow.xml"
        export_to_xml(c, str(xml_path))
        loaded = import_from_xml(str(xml_path))

        valid, reason = loaded.validate_structure()
        assert valid, reason

        table_after = get_truth_table(loaded)
        assert table_before == table_after


    def test_command_history_workflow(self):
        """Полный workflow undo/redo: подключение → undo → redo."""
        c = Circuit()
        history = CommandHistory()
        factory = CommandFactory(c)

        in0  = c.add_node("IN",  0,   0)
        out1 = c.add_node("OUT", 100, 0)

        cmd = factory.create_connect_pins(in0, 0, out1, 0)
        history.execute(cmd)
        assert len(c.connections) == 1

        history.undo()
        assert len(c.connections) == 0

        history.redo()
        assert len(c.connections) == 1


    def test_multiple_command_chain(self):
        """Цепочка из трёх connect-команд: полный undo → полный redo."""
        c = Circuit()
        history = CommandHistory()
        factory = CommandFactory(c)

        in0  = c.add_node("IN",  0,   0)
        in1  = c.add_node("IN",  0, 100)
        and1 = c.add_node("AND", 200, 50)
        out1 = c.add_node("OUT", 400, 50)

        for cmd in [
            factory.create_connect_pins(in0, 0, and1, 0),
            factory.create_connect_pins(in1, 0, and1, 1),
            factory.create_connect_pins(and1, 0, out1, 0),
        ]:
            history.execute(cmd)

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
        """XML roundtrip сохраняет количество узлов, связей и валидность схемы.

        Используется полная валидная схема (оба входа XOR подключены).
        """
        c, in0, in1, xor1, out1 = _xor_circuit()

        xml_path = tmp_path / "roundtrip.xml"
        export_to_xml(c, str(xml_path))
        loaded = import_from_xml(str(xml_path))

        assert len(loaded.get_nodes()) == len(c.get_nodes())
        assert len(loaded.connections) == len(c.connections)

        valid, reason = loaded.validate_structure()
        assert valid, reason


    def test_invalid_xml_raises_exception(self, tmp_path):
        """Повреждённый XML вызывает исключение при загрузке."""
        xml_path = tmp_path / "broken.xml"
        xml_path.write_text("<broken xml")

        with pytest.raises(Exception):
            import_from_xml(str(xml_path))


    def test_simplify_preserves_logic(self):
        """Упрощение схемы фиксирует вход, но сохраняет корректную логику.

        simplify() заменяет IN-узел на CONST_0/CONST_1, НЕ удаляя AND и
        другие узлы. Проверяем оба значения оставшегося входа.
        """
        c, in0, in1, and1, out1 = _and_circuit()

        # Фиксируем in0 = 1: AND(1, in1) = in1
        simplified = simplify(c, {in0: 1})
        nodes_by_id = {n["id"]: n for n in simplified.get_nodes()}

        # in0 заменён на CONST_1, остальные узлы остались
        assert nodes_by_id[in0]["type"] == "CONST_1"
        assert nodes_by_id[and1]["type"] == "AND"
        assert nodes_by_id[out1]["type"] == "OUT"

        # AND(CONST_1, 1) = 1
        assert evaluate_circuit(simplified, {in1: 1})[out1] == 1
        # AND(CONST_1, 0) = 0  ← второй случай обязателен
        assert evaluate_circuit(simplified, {in1: 0})[out1] == 0

    def test_simplify_with_zero_fixes_output(self):
        """Фиксация in0=0 делает AND всегда равным 0 независимо от in1."""
        c, in0, in1, and1, out1 = _and_circuit()

        simplified = simplify(c, {in0: 0})
        nodes_by_id = {n["id"]: n for n in simplified.get_nodes()}
        assert nodes_by_id[in0]["type"] == "CONST_0"

        # AND(0, 0) = 0 и AND(0, 1) = 0
        assert evaluate_circuit(simplified, {in1: 0})[out1] == 0
        assert evaluate_circuit(simplified, {in1: 1})[out1] == 0


    def test_large_circuit_evaluation(self):
        """Цепочка из 9 AND-вентилей (10 входов): AND(all=1) = 1."""
        c = Circuit()
        inputs = [c.add_node("IN", i * 50, 0) for i in range(10)]

        prev = inputs[0]
        for i in range(1, 10):
            gate = c.add_node("AND", i * 100, 50)
            c.connect_pins(prev, 0, gate, 0)
            c.connect_pins(inputs[i], 0, gate, 1)
            prev = gate

        out1 = c.add_node("OUT", 1100, 50)
        c.connect_pins(prev, 0, out1, 0)

        all_ones = {nid: 1 for nid in inputs}
        assert evaluate_circuit(c, all_ones)[out1] == 1

        # Если хоть один вход = 0, результат = 0
        one_zero = {**all_ones, inputs[5]: 0}
        assert evaluate_circuit(c, one_zero)[out1] == 0


    def test_loaded_circuit_matches_original_logic(self, tmp_path):
        """Загруженная схема вычисляется через id узлов загруженной схемы.

        После XML roundtrip узлы получают те же id (XML сохраняет id).
        Evaluate вызывается с id узлов из loaded, а не из оригинала.
        """
        c, in0, in1, xor1, out1 = _xor_circuit()

        original_result = evaluate_circuit(c, {in0: 1, in1: 0})[out1]  # XOR(1,0)=1

        xml_path = tmp_path / "logic.xml"
        export_to_xml(c, str(xml_path))
        loaded = import_from_xml(str(xml_path))

        # Получаем id входов/выходов из загруженной схемы
        loaded_in_ids  = _get_nodes_by_type(loaded, "IN")
        loaded_out_ids = _get_nodes_by_type(loaded, "OUT")
        l_in0, l_in1 = loaded_in_ids[0], loaded_in_ids[1]
        l_out1 = loaded_out_ids[0]

        loaded_result = evaluate_circuit(loaded, {l_in0: 1, l_in1: 0})[l_out1]
        assert loaded_result == original_result


    def test_truth_table_consistency_after_xml_roundtrip(self, tmp_path):
        """Truth table OR-схемы идентична до и после XML roundtrip."""
        c, in0, in1, or1, out1 = _or_circuit()

        before = get_truth_table(c)

        xml_path = tmp_path / "truth_table.xml"
        export_to_xml(c, str(xml_path))
        loaded = import_from_xml(str(xml_path))

        after = get_truth_table(loaded)
        assert before == after


    def test_redo_stack_cleared_after_new_command(self):
        """Новая команда после undo очищает redo-стек.

        После execute(cmd1) → undo → execute(cmd2):
          - cmd1 недоступен через redo (стек очищен)
          - redo() возвращает False и не меняет схему
          - в схеме только связь от cmd2
        """
        c = Circuit()
        history = CommandHistory()
        factory = CommandFactory(c)

        in0  = c.add_node("IN",  0,   0)
        out1 = c.add_node("OUT", 100, 0)
        out2 = c.add_node("OUT", 200, 0)

        cmd1 = factory.create_connect_pins(in0, 0, out1, 0)
        history.execute(cmd1)
        history.undo()
        assert len(c.connections) == 0

        cmd2 = factory.create_connect_pins(in0, 0, out2, 0)
        history.execute(cmd2)
        assert len(c.connections) == 1

        # redo-стек пуст — redo ничего не делает
        result = history.redo()
        assert result is False
        assert len(c.connections) == 1  # осталась только связь cmd2


    def test_complex_circuit_workflow(self, tmp_path):
        """Сложная схема (AND→XOR→OR): вычисление совпадает после XML roundtrip."""
        c = Circuit()
        in0  = c.add_node("IN",  0,   0)
        in1  = c.add_node("IN",  0, 100)
        in2  = c.add_node("IN",  0, 200)
        and1 = c.add_node("AND", 200,  50)
        xor1 = c.add_node("XOR", 400, 100)
        or1  = c.add_node("OR",  600, 100)
        out1 = c.add_node("OUT", 800, 100)

        c.connect_pins(in0, 0, and1, 0)
        c.connect_pins(in1, 0, and1, 1)
        c.connect_pins(and1, 0, xor1, 0)
        c.connect_pins(in2, 0, xor1, 1)
        c.connect_pins(xor1, 0, or1, 0)
        c.connect_pins(in0, 0, or1, 1)
        c.connect_pins(or1, 0, out1, 0)

        valid, reason = c.validate_structure()
        assert valid, reason

        # AND(1,1)=1, XOR(1,0)=1, OR(1,1)=1
        input_values = {in0: 1, in1: 1, in2: 0}
        result_before = evaluate_circuit(c, input_values)[out1]
        assert result_before == 1

        xml_path = tmp_path / "complex.xml"
        export_to_xml(c, str(xml_path))
        loaded = import_from_xml(str(xml_path))

        # Получаем id из загруженной схемы по типу и порядку
        l_inputs  = _get_nodes_by_type(loaded, "IN")
        l_outputs = _get_nodes_by_type(loaded, "OUT")
        l_in0, l_in1, l_in2 = l_inputs[0], l_inputs[1], l_inputs[2]
        l_out1 = l_outputs[0]

        result_after = evaluate_circuit(loaded, {l_in0: 1, l_in1: 1, l_in2: 0})[l_out1]
        assert result_before == result_after

        valid, reason = loaded.validate_structure()
        assert valid, reason