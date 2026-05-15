from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.model.elements import (
        AndNode,
        Const0Node,
        Const1Node,
        EqualNode,
        InputNode,
        OrNode,
        OutputNode,
        XorNode,
    )
    from backend.model.node import CircuitNode, SchemeComponent


class CircuitVisitor(ABC):
    """Базовый посетитель для обхода модели схемы (Visitor)."""

    def visit(self, component: SchemeComponent) -> None:
        component.accept(self)

    def visit_circuit(self, circuit) -> None:
        for component in circuit.iter_components():
            component.accept(self)

    def visit_node(self, node: CircuitNode) -> None:
        """Запасной маршрут для неизвестных типов."""
        self.visit_unknown(node)

    @abstractmethod
    def visit_input(self, node: InputNode) -> None:
        pass

    @abstractmethod
    def visit_output(self, node: OutputNode) -> None:
        pass

    @abstractmethod
    def visit_and(self, node: AndNode) -> None:
        pass

    @abstractmethod
    def visit_or(self, node: OrNode) -> None:
        pass

    @abstractmethod
    def visit_xor(self, node: XorNode) -> None:
        pass

    @abstractmethod
    def visit_equal(self, node: EqualNode) -> None:
        pass

    @abstractmethod
    def visit_const_0(self, node: Const0Node) -> None:
        pass

    @abstractmethod
    def visit_const_1(self, node: Const1Node) -> None:
        pass

    def visit_unknown(self, node: CircuitNode) -> None:
        pass
