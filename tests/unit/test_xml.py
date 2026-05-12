import pytest
import tempfile
import os
from backend.model.circuit import Circuit
from backend.io.xml_builder import export_to_xml, import_from_xml


def build_simple_circuit():
    """Вспомогательная функция: создаёт схему с двумя IN, AND и OUT."""
    c = Circuit()
    in1 = c.add_node("IN", 0, 0)
    in2 = c.add_node("IN", 0, 0)
    and1 = c.add_node("AND", 100, 100)
    out1 = c.add_node("OUT", 200, 200)
    c.connect_pins(in1, 0, and1, 0)
    c.connect_pins(in2, 0, and1, 1)
    c.connect_pins(and1, 0, out1, 0)
    return c


def test_export_import_roundtrip():
    """Сохраняем схему в XML, загружаем обратно и сравниваем узлы и связи."""
    c1 = build_simple_circuit()
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        path = f.name
    try:
        export_to_xml(c1, path)
        c2 = import_from_xml(path)

        # Сравниваем количество узлов
        assert len(c1.get_nodes()) == len(c2.get_nodes())

        # Переводим списки в словари по id для сравнения
        n1 = {n["id"]: n for n in c1.get_nodes()}
        n2 = {n["id"]: n for n in c2.get_nodes()}
        assert n1.keys() == n2.keys()

        for nid in n1:
            assert n1[nid]["type"] == n2[nid]["type"]
            assert n1[nid]["x"] == pytest.approx(n2[nid]["x"])
            assert n1[nid]["y"] == pytest.approx(n2[nid]["y"])

        # Сравниваем связи (списки кортежей)
        conns1 = sorted(c1.get_connections())
        conns2 = sorted(c2.get_connections())
        assert conns1 == conns2
    finally:
        os.unlink(path)  # удаляем временный файл


def test_import_invalid_xml():
    """Загружаем валидную пустую схему (без узлов) — ошибки быть не должно."""
    path = tempfile.mktemp(suffix=".xml")
    with open(path, "w") as f:
        f.write('<circuit><nodes/></circuit>')
    try:
        c = import_from_xml(path)
        assert len(c.get_nodes()) == 0
    finally:
        os.unlink(path)