"""
Тесты для модуля backend.logic.truth_table.

Проверяются функции:
  - get_truth_table         — таблица истинности всей схемы
  - get_truth_table_for_node — таблица истинности для отдельного узла
  - get_affected_nodes      — предки (влияющие узлы) данного узла
  - get_polynomials         — полиномиальное представление для всех узлов
  - get_polynomial_for_node — полином для одного узла
  - evaluate_circuit        — вычисление выходов при заданных входах
  - simplify                — упрощение схемы при фиксированных входах
  - get_removable_count_per_input — оценка количества удаляемых узлов
"""

import pytest
from backend.model.circuit import Circuit
from backend.logic.truth_table import (
    get_truth_table,
    get_truth_table_for_node,
    get_affected_nodes,
    get_polynomials,
    get_polynomial_for_node,
    evaluate_circuit,
    simplify,
    get_removable_count_per_input,
)


def _and_circuit():
    """IN0, IN1 → AND → OUT. Возвращает (circuit, in0, in1, and_id, out_id)."""
    c = Circuit()
    in0 = c.add_node("IN", 0, 0)
    in1 = c.add_node("IN", 50, 0)
    and1 = c.add_node("AND", 100, 0)
    out1 = c.add_node("OUT", 150, 0)
    c.connect_pins(in0, 0, and1, 0)
    c.connect_pins(in1, 0, and1, 1)
    c.connect_pins(and1, 0, out1, 0)
    return c, in0, in1, and1, out1


def _or_circuit():
    """IN0, IN1 → OR → OUT."""
    c = Circuit()
    in0 = c.add_node("IN", 0, 0)
    in1 = c.add_node("IN", 50, 0)
    or1 = c.add_node("OR", 100, 0)
    out1 = c.add_node("OUT", 150, 0)
    c.connect_pins(in0, 0, or1, 0)
    c.connect_pins(in1, 0, or1, 1)
    c.connect_pins(or1, 0, out1, 0)
    return c, in0, in1, or1, out1


def _xor_circuit():
    """IN0, IN1 → XOR → OUT."""
    c = Circuit()
    in0 = c.add_node("IN", 0, 0)
    in1 = c.add_node("IN", 50, 0)
    xor1 = c.add_node("XOR", 100, 0)
    out1 = c.add_node("OUT", 150, 0)
    c.connect_pins(in0, 0, xor1, 0)
    c.connect_pins(in1, 0, xor1, 1)
    c.connect_pins(xor1, 0, out1, 0)
    return c, in0, in1, xor1, out1


def _equal_circuit():
    """IN0, IN1 → EQUAL → OUT."""
    c = Circuit()
    in0 = c.add_node("IN", 0, 0)
    in1 = c.add_node("IN", 50, 0)
    eq1 = c.add_node("EQUAL", 100, 0)
    out1 = c.add_node("OUT", 150, 0)
    c.connect_pins(in0, 0, eq1, 0)
    c.connect_pins(in1, 0, eq1, 1)
    c.connect_pins(eq1, 0, out1, 0)
    return c, in0, in1, eq1, out1


def _rows_as_tuples(rows, in_ids, out_ids):
    """Превращает список dict-строк в список кортежей (in_values, out_values)."""
    result = []
    for row in rows:
        ins = tuple(row[f"IN_{i}"] for i in in_ids)
        outs = tuple(row[f"OUT_{o}"] for o in out_ids)
        result.append((ins, outs))
    return result



class TestGetTruthTable:

    def test_and_gate_truth_table(self):
        """AND: выход равен 1 только при обоих входах = 1."""
        c, in0, in1, and1, out1 = _and_circuit()
        tt = get_truth_table(c)

        assert sorted(tt["inputs"]) == sorted([in0, in1])
        assert tt["outputs"] == [out1]
        assert len(tt["rows"]) == 4

        rows = _rows_as_tuples(tt["rows"], tt["inputs"], tt["outputs"])
        # Формируем ожидаемую таблицу через AND
        for ins, outs in rows:
            expected = 1 if all(ins) else 0
            assert outs[0] == expected

    def test_or_gate_truth_table(self):
        """OR: выход равен 1, если хотя бы один вход = 1."""
        c, in0, in1, or1, out1 = _or_circuit()
        tt = get_truth_table(c)

        rows = _rows_as_tuples(tt["rows"], tt["inputs"], tt["outputs"])
        for ins, outs in rows:
            expected = 1 if any(ins) else 0
            assert outs[0] == expected

    def test_xor_gate_truth_table(self):
        """XOR: выход равен 1, если входы различны."""
        c, in0, in1, xor1, out1 = _xor_circuit()
        tt = get_truth_table(c)

        rows = _rows_as_tuples(tt["rows"], tt["inputs"], tt["outputs"])
        for ins, outs in rows:
            expected = ins[0] ^ ins[1]
            assert outs[0] == expected

    def test_equal_gate_truth_table(self):
        """EQUAL: выход равен 1, если оба входа совпадают."""
        c, in0, in1, eq1, out1 = _equal_circuit()
        tt = get_truth_table(c)

        rows = _rows_as_tuples(tt["rows"], tt["inputs"], tt["outputs"])
        for ins, outs in rows:
            expected = 1 if ins[0] == ins[1] else 0
            assert outs[0] == expected

    def test_row_count_is_power_of_two(self):
        """Количество строк равно 2^(число входов)."""
        c, in0, in1, and1, out1 = _and_circuit()
        # Добавляем третий вход через OR после AND
        in2 = c.add_node("IN", 0, 100)
        or1 = c.add_node("OR", 200, 0)
        out2 = c.add_node("OUT", 300, 0)
        c.connect_pins(and1, 0, or1, 0)
        c.connect_pins(in2, 0, or1, 1)
        c.connect_pins(or1, 0, out2, 0)
        # Убираем старый out1, схема теперь выглядит иначе - добавим ещё
        # Простой случай: 3 входа дают 8 строк
        c2 = Circuit()
        i0 = c2.add_node("IN", 0, 0)
        i1 = c2.add_node("IN", 50, 0)
        i2 = c2.add_node("IN", 100, 0)
        a1 = c2.add_node("AND", 150, 0)
        a2 = c2.add_node("AND", 200, 0)
        o = c2.add_node("OUT", 250, 0)
        c2.connect_pins(i0, 0, a1, 0)
        c2.connect_pins(i1, 0, a1, 1)
        c2.connect_pins(a1, 0, a2, 0)
        c2.connect_pins(i2, 0, a2, 1)
        c2.connect_pins(a2, 0, o, 0)
        tt = get_truth_table(c2)
        assert len(tt["rows"]) == 8

    def test_empty_circuit_returns_empty_rows(self):
        """Пустая схема (без IN/OUT) возвращает пустой список строк."""
        c = Circuit()
        tt = get_truth_table(c)
        assert tt["rows"] == []

    def test_circuit_with_const_node(self):
        """Схема с CONST_1 на входе AND: таблица зависит только от оставшегося IN."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        const1 = c.add_node("CONST_1", 50, 0)
        and1 = c.add_node("AND", 100, 0)
        out1 = c.add_node("OUT", 150, 0)
        c.connect_pins(in0, 0, and1, 0)
        c.connect_pins(const1, 0, and1, 1)
        c.connect_pins(and1, 0, out1, 0)
        tt = get_truth_table(c)
        # Только один IN → 2 строки
        assert len(tt["rows"]) == 2
        # AND(in0, 1) = in0
        for row in tt["rows"]:
            assert row[f"OUT_{out1}"] == row[f"IN_{in0}"]



class TestGetTruthTableForNode:

    def test_truth_table_for_gate_node(self):
        """Таблица для AND-узла совпадает с AND-функцией."""
        c, in0, in1, and1, out1 = _and_circuit()
        tt = get_truth_table_for_node(c, and1)

        assert tt["node_id"] == and1
        assert len(tt["rows"]) == 4
        for row in tt["rows"]:
            expected = row[f"IN_{in0}"] & row[f"IN_{in1}"]
            assert row[f"Node_{and1}"] == expected

    def test_truth_table_for_input_node(self):
        """Таблица для узла IN содержит только его самого."""
        c, in0, in1, and1, out1 = _and_circuit()
        tt = get_truth_table_for_node(c, in0)

        assert tt["node_id"] == in0
        # Ключ строки — Node_{in0}
        for row in tt["rows"]:
            assert f"Node_{in0}" in row

    def test_truth_table_for_output_node(self):
        """Таблица для OUT-узла совпадает с полной таблицей схемы."""
        c, in0, in1, and1, out1 = _and_circuit()
        tt_node = get_truth_table_for_node(c, out1)
        tt_full = get_truth_table(c)

        assert len(tt_node["rows"]) == len(tt_full["rows"])
        for row_n, row_f in zip(tt_node["rows"], tt_full["rows"]):
            assert row_n[f"Node_{out1}"] == row_f[f"OUT_{out1}"]

    def test_nonexistent_node_returns_empty(self):
        """Запрос для несуществующего узла возвращает пустые строки."""
        c, *_ = _and_circuit()
        tt = get_truth_table_for_node(c, 9999)
        assert tt["rows"] == []


class TestGetAffectedNodes:

    def test_output_node_affected_by_all(self):
        """OUT зависит от IN0, IN1 и AND."""
        c, in0, in1, and1, out1 = _and_circuit()
        affected = get_affected_nodes(c, out1)

        assert in0 in affected
        assert in1 in affected
        assert and1 in affected

    def test_and_gate_affected_by_inputs(self):
        """AND зависит от IN0 и IN1."""
        c, in0, in1, and1, out1 = _and_circuit()
        affected = get_affected_nodes(c, and1)

        assert in0 in affected
        assert in1 in affected
        assert out1 not in affected

    def test_input_node_has_no_ancestors(self):
        """IN не имеет предков."""
        c, in0, in1, and1, out1 = _and_circuit()
        affected = get_affected_nodes(c, in0)
        assert affected == []

    def test_chained_gates_affected(self):
        """В цепочке AND→OR узел OR зависит от всех предыдущих."""
        c = Circuit()
        i0 = c.add_node("IN", 0, 0)
        i1 = c.add_node("IN", 50, 0)
        i2 = c.add_node("IN", 0, 100)
        a1 = c.add_node("AND", 100, 0)
        or1 = c.add_node("OR", 200, 0)
        out = c.add_node("OUT", 300, 0)
        c.connect_pins(i0, 0, a1, 0)
        c.connect_pins(i1, 0, a1, 1)
        c.connect_pins(a1, 0, or1, 0)
        c.connect_pins(i2, 0, or1, 1)
        c.connect_pins(or1, 0, out, 0)

        affected = get_affected_nodes(c, or1)
        assert i0 in affected
        assert i1 in affected
        assert i2 in affected
        assert a1 in affected


class TestPolynomials:

    def test_input_node_polynomial(self):
        """Полином входного узла — его переменная x<id>."""
        c, in0, in1, and1, out1 = _and_circuit()
        polys = get_polynomials(c)
        assert polys[in0] == f"x{in0}"
        assert polys[in1] == f"x{in1}"

    def test_and_gate_polynomial(self):
        """AND: полином использует оператор *."""
        c, in0, in1, and1, out1 = _and_circuit()
        poly = get_polynomial_for_node(c, and1)
        assert "*" in poly
        assert f"x{in0}" in poly
        assert f"x{in1}" in poly

    def test_or_gate_polynomial(self):
        """OR: полином использует оператор +."""
        c, in0, in1, or1, out1 = _or_circuit()
        poly = get_polynomial_for_node(c, or1)
        assert "+" in poly

    def test_xor_gate_polynomial(self):
        """XOR: полином использует оператор ^."""
        c, in0, in1, xor1, out1 = _xor_circuit()
        poly = get_polynomial_for_node(c, xor1)
        assert "^" in poly
        assert "x" in poly


    def test_equal_gate_polynomial(self):
        """EQUAL/XNOR: полином использует ~^ или эквивалент."""
        c, in0, in1, eq1, out1 = _equal_circuit()
        poly = get_polynomial_for_node(c, eq1)
        assert "~^" in poly or "==" in poly or "≡" in poly or "=" in poly

    def test_output_node_polynomial_equals_source(self):
        """Полином OUT равен полиному его единственного источника."""
        c, in0, in1, and1, out1 = _and_circuit()
        polys = get_polynomials(c)
        assert polys[out1] == polys[and1]

    def test_const0_polynomial(self):
        """CONST_0 имеет полином '0'."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        const0 = c.add_node("CONST_0", 50, 0)
        or1 = c.add_node("OR", 100, 0)
        out1 = c.add_node("OUT", 150, 0)
        c.connect_pins(in0, 0, or1, 0)
        c.connect_pins(const0, 0, or1, 1)
        c.connect_pins(or1, 0, out1, 0)
        polys = get_polynomials(c)
        assert polys[const0] == "0"

    def test_const1_polynomial(self):
        """CONST_1 имеет полином '1'."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        const1 = c.add_node("CONST_1", 50, 0)
        and1 = c.add_node("AND", 100, 0)
        out1 = c.add_node("OUT", 150, 0)
        c.connect_pins(in0, 0, and1, 0)
        c.connect_pins(const1, 0, and1, 1)
        c.connect_pins(and1, 0, out1, 0)
        polys = get_polynomials(c)
        assert polys[const1] == "1"

    def test_get_polynomials_covers_all_nodes(self):
        """get_polynomials возвращает полином для каждого узла схемы."""
        c, in0, in1, and1, out1 = _and_circuit()
        polys = get_polynomials(c)
        for node in c.get_nodes():
            assert node["id"] in polys


class TestEvaluateCircuit:

    def test_and_both_true(self):
        """AND(1, 1) = 1."""
        c, in0, in1, and1, out1 = _and_circuit()
        result = evaluate_circuit(c, {in0: 1, in1: 1})
        assert result[out1] == 1

    def test_and_one_false(self):
        """AND(1, 0) = 0."""
        c, in0, in1, and1, out1 = _and_circuit()
        result = evaluate_circuit(c, {in0: 1, in1: 0})
        assert result[out1] == 0

    def test_or_one_true(self):
        """OR(0, 1) = 1."""
        c, in0, in1, or1, out1 = _or_circuit()
        result = evaluate_circuit(c, {in0: 0, in1: 1})
        assert result[out1] == 1

    def test_or_both_false(self):
        """OR(0, 0) = 0."""
        c, in0, in1, or1, out1 = _or_circuit()
        result = evaluate_circuit(c, {in0: 0, in1: 0})
        assert result[out1] == 0

    def test_xor_different_inputs(self):
        """XOR(1, 0) = 1."""
        c, in0, in1, xor1, out1 = _xor_circuit()
        result = evaluate_circuit(c, {in0: 1, in1: 0})
        assert result[out1] == 1

    def test_xor_same_inputs(self):
        """XOR(1, 1) = 0."""
        c, in0, in1, xor1, out1 = _xor_circuit()
        result = evaluate_circuit(c, {in0: 1, in1: 1})
        assert result[out1] == 0

    def test_equal_same_inputs(self):
        """EQUAL(0, 0) = 1."""
        c, in0, in1, eq1, out1 = _equal_circuit()
        result = evaluate_circuit(c, {in0: 0, in1: 0})
        assert result[out1] == 1

    def test_equal_different_inputs(self):
        """EQUAL(0, 1) = 0."""
        c, in0, in1, eq1, out1 = _equal_circuit()
        result = evaluate_circuit(c, {in0: 0, in1: 1})
        assert result[out1] == 0

    def test_result_contains_only_output_nodes(self):
        """evaluate_circuit возвращает только OUT-узлы."""
        c, in0, in1, and1, out1 = _and_circuit()
        result = evaluate_circuit(c, {in0: 1, in1: 1})
        assert set(result.keys()) == {out1}

    def test_evaluate_all_combinations_consistent_with_truth_table(self):
        """evaluate_circuit согласован с get_truth_table для всех комбинаций."""
        c, in0, in1, and1, out1 = _and_circuit()
        tt = get_truth_table(c)
        for row in tt["rows"]:
            iv = {in0: row[f"IN_{in0}"], in1: row[f"IN_{in1}"]}
            result = evaluate_circuit(c, iv)
            assert result[out1] == row[f"OUT_{out1}"]


class TestSimplify:

    def test_simplify_replaces_input_with_const0(self):
        """Фиксация IN=0 заменяет узел на CONST_0."""
        c, in0, in1, and1, out1 = _and_circuit()
        s = simplify(c, {in0: 0})
        nodes_by_id = {n["id"]: n for n in s.get_nodes()}
        assert nodes_by_id[in0]["type"] == "CONST_0"

    def test_simplify_replaces_input_with_const1(self):
        """Фиксация IN=1 заменяет узел на CONST_1."""
        c, in0, in1, and1, out1 = _and_circuit()
        s = simplify(c, {in0: 1})
        nodes_by_id = {n["id"]: n for n in s.get_nodes()}
        assert nodes_by_id[in0]["type"] == "CONST_1"

    def test_simplify_does_not_mutate_original(self):
        """Упрощение не изменяет исходную схему."""
        c, in0, in1, and1, out1 = _and_circuit()
        original_node_count = len(c.get_nodes())
        original_in0_type = c.get_node(in0)["type"]

        simplify(c, {in0: 0})

        assert len(c.get_nodes()) == original_node_count
        assert c.get_node(in0)["type"] == original_in0_type

    def test_simplify_returns_circuit_instance(self):
        """simplify возвращает объект Circuit."""
        c, in0, in1, and1, out1 = _and_circuit()
        s = simplify(c, {in0: 0})
        assert isinstance(s, Circuit)

    def test_simplify_multiple_inputs(self):
        """Можно зафиксировать несколько входов одновременно."""
        c, in0, in1, and1, out1 = _and_circuit()
        s = simplify(c, {in0: 1, in1: 0})
        nodes_by_id = {n["id"]: n for n in s.get_nodes()}
        assert nodes_by_id[in0]["type"] == "CONST_1"
        assert nodes_by_id[in1]["type"] == "CONST_0"

    def test_simplified_circuit_is_valid(self):
        """Упрощённая схема проходит validate_structure."""
        c, in0, in1, and1, out1 = _and_circuit()
        s = simplify(c, {in0: 0})
        valid, reason = s.validate_structure()
        assert valid, reason


class TestGetRemovableCountPerInput:

    def test_returns_dict_for_each_input(self):
        """Функция возвращает запись для каждого входного узла."""
        c, in0, in1, and1, out1 = _and_circuit()
        result = get_removable_count_per_input(c)

        assert in0 in result
        assert in1 in result

    def test_each_entry_has_if0_and_if1(self):
        """Каждая запись содержит ключи 'if_0' и 'if_1'."""
        c, in0, in1, and1, out1 = _and_circuit()
        result = get_removable_count_per_input(c)

        for nid, counts in result.items():
            assert "if_0" in counts, f"'if_0' missing for node {nid}"
            assert "if_1" in counts, f"'if_1' missing for node {nid}"

    def test_counts_are_non_negative(self):
        """Количество удаляемых узлов не может быть отрицательным."""
        c, in0, in1, and1, out1 = _and_circuit()
        result = get_removable_count_per_input(c)

        for nid, counts in result.items():
            assert counts["if_0"] >= 0
            assert counts["if_1"] >= 0

    def test_no_inputs_returns_empty(self):
        """Схема без IN-узлов даёт пустой словарь."""
        c = Circuit()
        c.add_node("AND", 0, 0)
        result = get_removable_count_per_input(c)
        assert result == {}

    def test_const_input_circuit_has_input_entry(self):
        """Схема с CONST содержит запись только для IN-узлов."""
        c = Circuit()
        in0 = c.add_node("IN", 0, 0)
        const1 = c.add_node("CONST_1", 50, 0)
        and1 = c.add_node("AND", 100, 0)
        out1 = c.add_node("OUT", 150, 0)
        c.connect_pins(in0, 0, and1, 0)
        c.connect_pins(const1, 0, and1, 1)
        c.connect_pins(and1, 0, out1, 0)
        result = get_removable_count_per_input(c)
        assert in0 in result
        assert const1 not in result
