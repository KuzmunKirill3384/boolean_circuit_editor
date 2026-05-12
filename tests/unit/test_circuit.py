import pytest
from backend.model.circuit import Circuit


def test_add_node():
    """Проверяем, что узел добавляется и сохраняет тип и координаты."""
    c = Circuit()
    nid = c.add_node("AND", 100, 200)
    node = c.get_node(nid)
    assert node["type"] == "AND"
    assert node["x"] == 100.0
    assert node["y"] == 200.0


def test_add_node_invalid_type():
    """Проверяем, что нельзя добавить узел с несуществующим типом."""
    c = Circuit()
    with pytest.raises(ValueError):
        c.add_node("NAND", 0, 0)


def test_connect_pins():
    """Проверяем соединение пинов и запрет повторного подключения к тому же входу."""
    c = Circuit()
    n1 = c.add_node("IN", 0, 0)
    n2 = c.add_node("AND", 0, 0)
    n3 = c.add_node("OUT", 0, 0)
    # Соединяем вход с AND
    ok, msg = c.connect_pins(n1, 0, n2, 0)
    assert ok  # должно пройти успешно
    # Соединяем AND с OUT
    assert c.connect_pins(n2, 0, n3, 0)[0]
    # Пытаемся подключить другой IN к тому же входному пину AND (0) — нельзя
    n4 = c.add_node("IN", 0, 0)
    ok, msg = c.connect_pins(n4, 0, n2, 0)
    assert not ok


def test_cycle_detection():
    """Проверяем, что соединение, создающее цикл, запрещено."""
    c = Circuit()
    n1 = c.add_node("AND", 0, 0)
    n2 = c.add_node("OR", 0, 0)
    c.connect_pins(n1, 0, n2, 0)
    valid, msg = c.validate_connection(n2, 0, n1, 0)
    assert not valid
    assert "cycle" in msg.lower()


def test_remove_node():
    """Проверяем удаление узла и автоматическое удаление его связей."""
    c = Circuit()
    n1 = c.add_node("IN", 0, 0)
    n2 = c.add_node("OUT", 0, 0)
    c.connect_pins(n1, 0, n2, 0)
    c.remove_node(n2)
    # Узел должен исчезнуть
    assert c.get_node(n2) is None
    # Связи, где он участвовал, тоже должны исчезнуть
    assert len(c.get_connections()) == 0


def test_validate_structure():
    """Проверяем валидацию: схема без ошибок валидна, схема с циклом — нет."""
    c = Circuit()
    n1 = c.add_node("IN", 0, 0)
    n2 = c.add_node("OUT", 0, 0)
    # Даже без соединений структура валидна (допустимо при редактировании)
    v, reason = c.validate_structure()
    assert v
    # Добавим связь — тоже валидна
    c.connect_pins(n1, 0, n2, 0)
    v, reason = c.validate_structure()
    assert v
    # Создадим цикл и проверим, что структура стала невалидной
    n3 = c.add_node("AND", 0, 0)
    c.connect_pins(n2, 0, n3, 0)  # OUT -> AND (но OUT не имеет выходов, это запрещено)
    # Вместо этого построим цикл по-другому: два AND соединим в кольцо
    c2 = Circuit()
    a1 = c2.add_node("AND", 0, 0)
    a2 = c2.add_node("AND", 0, 0)
    c2.connect_pins(a1, 0, a2, 0)
    # Пытаемся замкнуть
    ok, _ = c2.connect_pins(a2, 0, a1, 0)
    # Либо соединение запрещено на уровне connect_pins, либо validate_structure найдёт цикл
    if ok:
        v, reason = c2.validate_structure()
        assert not v