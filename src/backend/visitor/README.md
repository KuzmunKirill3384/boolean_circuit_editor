# Backend Visitor

Обход модели по паттерну **Visitor**:

- `visitor.py` — `CircuitVisitor` и `visit_circuit()`
- `node_roles.py` — `NodeRolesVisitor` (сбор IN/OUT), используется в `truth_table`

Используется для:

- do/undo-команд;
- вычислений на графе схемы;
- расширяемого обхода без захламления самих узлов.
