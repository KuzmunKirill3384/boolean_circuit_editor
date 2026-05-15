from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.visitor.visitor import CircuitVisitor


class SchemeComponent(ABC):
    """Базовый компонент модели схемы (Composite)."""

    @abstractmethod
    def accept(self, visitor: CircuitVisitor) -> None:
        pass

    @property
    @abstractmethod
    def node_id(self) -> int:
        pass

    @property
    @abstractmethod
    def node_type(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass


class CircuitNode(SchemeComponent):
    """Листовой узел схемы; хранит id, тип и координаты."""

    def __init__(self, data: dict[str, Any]):
        self._data = dict(data)
        self._data["type"] = str(self._data["type"]).upper()

    @property
    def node_id(self) -> int:
        return int(self._data["id"])

    @property
    def node_type(self) -> str:
        return self._data["type"]

    @property
    def x(self) -> float:
        return float(self._data["x"])

    @property
    def y(self) -> float:
        return float(self._data["y"])

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def accept(self, visitor: CircuitVisitor) -> None:
        visitor.visit_node(self)
