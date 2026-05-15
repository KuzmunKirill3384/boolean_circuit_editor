# Backend Model

Модель схемы по паттерну **Composite**:

- `node.py` — `SchemeComponent`, лист `CircuitNode`
- `elements.py` — типизированные узлы (`InputNode`, `AndNode`, …) с `accept(visitor)`
- `circuit.py` — контейнер `Circuit` (Composite), связи между пинами

Планируемое содержимое:

- базовый узел схемы;
- логические элементы;
- входы и выходы;
- контейнер схемы и связи между узлами.
