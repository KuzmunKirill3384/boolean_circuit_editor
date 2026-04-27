import itertools

def get_truth_table(circuit):
    # пример заглушки
    return {"inputs": [], "outputs": []}

def get_truth_table_for_node(node):
    # пример заглушки
    return {"node": node, "truth_table": []}

def get_affected_nodes(node, graph):
    # пример: возвращает связанные узлы
    return graph.get(node, [])