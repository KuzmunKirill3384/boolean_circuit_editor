
class Circuit:
    def __init__(self):
        self.nodes = []  # список узлов
        self.connections = []  # список соединений
        
    def add_node(self, node_type, x, y):
        # TODO: реализовать добавление узла
        pass
    
    def connect_nodes(self, out_node_id, in_node_id):
        # TODO: реализовать соединение узлов
        pass
    
    def get_nodes(self):
        return self.nodes
    
    def get_connections(self):
        return self.connections