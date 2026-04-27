from __future__ import annotations

import copy
import itertools
from typing import Any


def _normalize_type(node_type: str) -> str:
    return (node_type or "").upper()


def _node_map(circuit: Any) -> dict[int, dict[str, Any]]:
    return {n["id"]: n for n in circuit.get_nodes()}


def _incoming(circuit: Any) -> dict[int, list[tuple[int, int, int, int]]]:
    inc: dict[int, list[tuple[int, int, int, int]]] = {}
    for conn in circuit.get_connections():
        out_id, out_pin, in_id, in_pin = conn
        inc.setdefault(in_id, []).append((out_id, out_pin, in_id, in_pin))
    for in_id in inc:
        inc[in_id].sort(key=lambda c: c[3])  # by input pin index
    return inc


def _required_input_count(circuit: Any, node_type: str) -> int:
    in_count, _ = circuit.get_pin_counts(node_type)
    return int(in_count)


def _outgoing(circuit: Any) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for out_id, _out_pin, in_id, _in_pin in circuit.get_connections():
        out.setdefault(out_id, []).append(in_id)
    return out


def _evaluate_gate(gate_type: str, values: list[int]) -> int:
    t = _normalize_type(gate_type)
    if t == "AND":
        return 1 if all(values) else 0
    if t == "OR":
        return 1 if any(values) else 0
    if t == "XOR":
        return sum(values) % 2
    if t == "EQUAL":
        return 1 if len(set(values)) <= 1 else 0
    raise ValueError(f"Unknown gate type: {gate_type}")


def _evaluate_all(circuit: Any, input_values: dict[int, int]) -> dict[int, int]:
    nodes = _node_map(circuit)
    incoming = _incoming(circuit)
    cache: dict[int, int] = {}
    visiting: set[int] = set()

    def resolve(node_id: int) -> int:
        if node_id in cache:
            return cache[node_id]
        if node_id in visiting:
            raise ValueError("Cycle detected during evaluation")
        visiting.add(node_id)

        node = nodes.get(node_id)
        if node is None:
            visiting.remove(node_id)
            raise ValueError(f"Node {node_id} not found")

        node_type = _normalize_type(node["type"])
        if node_type == "IN":
            value = int(input_values.get(node_id, 0))
        elif node_type == "CONST_0":
            value = 0
        elif node_type == "CONST_1":
            value = 1
        elif node_type == "OUT":
            source = next((c for c in incoming.get(node_id, []) if c[3] == 0), None)
            if source is None:
                raise ValueError(f"Output node {node_id} has no input connection")
            if len(incoming.get(node_id, [])) > 1:
                raise ValueError(f"Output node {node_id} has multiple input connections")
            value = resolve(source[0])
        else:
            conns = incoming.get(node_id, [])
            if not conns:
                raise ValueError(f"Gate node {node_id} has no input connections")
            required = _required_input_count(circuit, node_type)
            expected_pins = set(range(required))
            actual_pins = {c[3] for c in conns}
            if expected_pins != actual_pins:
                missing = sorted(expected_pins - actual_pins)
                raise ValueError(f"Gate node {node_id} has unconnected input pins: {missing}")
            if len(conns) > required:
                raise ValueError(f"Gate node {node_id} has too many input connections")
            values = [resolve(c[0]) for c in conns]
            value = _evaluate_gate(node_type, values)

        cache[node_id] = int(value)
        visiting.remove(node_id)
        return cache[node_id]

    for nid in nodes:
        resolve(nid)
    return cache


def _collect_ancestors(circuit: Any, node_id: int) -> list[int]:
    incoming = _incoming(circuit)
    visited: set[int] = set()

    def dfs(nid: int) -> None:
        for out_id, _out_pin, _in_id, _in_pin in incoming.get(nid, []):
            if out_id not in visited:
                visited.add(out_id)
                dfs(out_id)

    dfs(node_id)
    return sorted(visited)


def get_truth_table(circuit: Any) -> dict[str, Any]:
    valid, reason = circuit.validate_structure()
    if not valid:
        raise ValueError(reason)

    nodes = circuit.get_nodes()
    inputs = sorted([n["id"] for n in nodes if _normalize_type(n["type"]) == "IN"])
    outputs = sorted([n["id"] for n in nodes if _normalize_type(n["type"]) == "OUT"])
    if not inputs or not outputs:
        return {"inputs": inputs, "outputs": outputs, "rows": []}

    rows: list[dict[str, int]] = []
    for bits in itertools.product([0, 1], repeat=len(inputs)):
        in_values = {nid: bits[idx] for idx, nid in enumerate(inputs)}
        evaluated = _evaluate_all(circuit, in_values)
        row: dict[str, int] = {}
        for nid in inputs:
            row[f"IN_{nid}"] = int(in_values[nid])
        for nid in outputs:
            row[f"OUT_{nid}"] = int(evaluated.get(nid, 0))
        rows.append(row)
    return {"inputs": inputs, "outputs": outputs, "rows": rows}


def get_truth_table_for_node(circuit: Any, node_id: int) -> dict[str, Any]:
    valid, reason = circuit.validate_structure()
    if not valid:
        raise ValueError(reason)

    node = circuit.get_node(node_id)
    if node is None:
        return {"inputs": [], "node_id": node_id, "rows": []}

    affected = _collect_ancestors(circuit, node_id)
    input_ids = sorted(
        nid
        for nid in affected
        if _normalize_type(circuit.get_node(nid)["type"]) == "IN"
    )
    if _normalize_type(node["type"]) == "IN" and node_id not in input_ids:
        input_ids.append(node_id)
    input_ids = sorted(input_ids)

    rows: list[dict[str, int]] = []
    for bits in itertools.product([0, 1], repeat=len(input_ids)):
        in_values = {nid: bits[idx] for idx, nid in enumerate(input_ids)}
        evaluated = _evaluate_all(circuit, in_values)
        row: dict[str, int] = {}
        for nid in input_ids:
            row[f"IN_{nid}"] = int(in_values[nid])
        row[f"Node_{node_id}"] = int(evaluated.get(node_id, 0))
        rows.append(row)
    return {"inputs": input_ids, "node_id": node_id, "rows": rows}


def get_affected_nodes(circuit: Any, node_id: int) -> list[int]:
    return _collect_ancestors(circuit, node_id)


def _polynomial_for_node(circuit: Any, node_id: int, memo: dict[int, str]) -> str:
    if node_id in memo:
        return memo[node_id]
    node = circuit.get_node(node_id)
    if node is None:
        return f"?{node_id}"
    t = _normalize_type(node["type"])
    incoming = _incoming(circuit).get(node_id, [])

    if t == "IN":
        expr = f"x{node_id}"
    elif t == "CONST_0":
        expr = "0"
    elif t == "CONST_1":
        expr = "1"
    elif t == "OUT":
        src = next((c for c in incoming if c[3] == 0), None)
        expr = _polynomial_for_node(circuit, src[0], memo) if src else "?"
    else:
        args = [_polynomial_for_node(circuit, c[0], memo) for c in incoming]
        op = {"AND": "*", "OR": "+", "XOR": "⊕", "EQUAL": "="}.get(t, t)
        expr = f"({f' {op} '.join(args)})" if args else f"{t}(?)"

    memo[node_id] = expr
    return expr


def get_polynomials(circuit: Any) -> dict[int, str]:
    valid, reason = circuit.validate_structure()
    if not valid:
        raise ValueError(reason)

    memo: dict[int, str] = {}
    result: dict[int, str] = {}
    for n in circuit.get_nodes():
        result[n["id"]] = _polynomial_for_node(circuit, n["id"], memo)
    return result


def get_polynomial_for_node(circuit: Any, node_id: int) -> str:
    valid, reason = circuit.validate_structure()
    if not valid:
        raise ValueError(reason)
    return _polynomial_for_node(circuit, node_id, {})


def evaluate_circuit(circuit: Any, input_values: dict[int, int]) -> dict[int, int]:
    valid, reason = circuit.validate_structure()
    if not valid:
        raise ValueError(reason)
    values = _evaluate_all(circuit, {k: int(v) for k, v in input_values.items()})
    outputs = [n["id"] for n in circuit.get_nodes() if _normalize_type(n["type"]) == "OUT"]
    return {oid: int(values.get(oid, 0)) for oid in outputs}


def _reachable_from_outputs(circuit: Any) -> set[int]:
    outputs = [n["id"] for n in circuit.get_nodes() if _normalize_type(n["type"]) == "OUT"]
    incoming = _incoming(circuit)
    reachable: set[int] = set(outputs)
    stack = outputs[:]
    while stack:
        nid = stack.pop()
        for src_id, _out_pin, _to, _to_pin in incoming.get(nid, []):
            if src_id not in reachable:
                reachable.add(src_id)
                stack.append(src_id)
    return reachable


def simplify(circuit: Any, input_values: dict[int, int]) -> Any:
    """Упрощение в безопасном виде: убираем узлы, не влияющие на выходы.

    Дополнительно, если вход фиксирован, можно заменить его на CONST_0/CONST_1.
    """
    new_circuit = copy.deepcopy(circuit)
    valid, reason = new_circuit.validate_structure()
    if not valid:
        raise ValueError(reason)
    fixed = {int(k): int(v) for k, v in input_values.items()}

    # Замена фиксированных входов на константы.
    for node in new_circuit.get_nodes():
        if _normalize_type(node["type"]) == "IN" and node["id"] in fixed:
            node["type"] = "CONST_1" if fixed[node["id"]] else "CONST_0"

    reachable = _reachable_from_outputs(new_circuit)
    for node in list(new_circuit.get_nodes()):
        if node["id"] not in reachable:
            new_circuit.remove_node(node["id"])
    return new_circuit


def get_removable_count_per_input(circuit: Any, _input_values: dict[int, int] | None = None) -> dict[int, dict[str, int]]:
    """Оценка, сколько узлов удалится при фиксации каждого входа в 0/1."""
    valid, reason = circuit.validate_structure()
    if not valid:
        raise ValueError(reason)

    result: dict[int, dict[str, int]] = {}
    input_ids = [n["id"] for n in circuit.get_nodes() if _normalize_type(n["type"]) == "IN"]
    base_count = len(circuit.get_nodes())
    for nid in input_ids:
        c0 = simplify(circuit, {nid: 0})
        c1 = simplify(circuit, {nid: 1})
        result[nid] = {
            "if_0": max(0, base_count - len(c0.get_nodes())),
            "if_1": max(0, base_count - len(c1.get_nodes())),
        }
    return result