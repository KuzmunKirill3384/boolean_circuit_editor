from PyQt6.QtWidgets import QGraphicsScene

class CircuitScene(QGraphicsScene):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setSceneRect(0, 0, 1000, 600)
    
    def sync_scene(self):
        """Синхронизация сцены с моделью данных"""
        # TODO: реализовать синхронизацию
        print("Синхронизация сцены")
        pass