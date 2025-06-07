# Placeholder for ActivationWorker
# TODO: Implement activation sequence logic with current cycling

from PyQt5.QtCore import QThread, pyqtSignal

class ActivationWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, resource_name):
        super().__init__()
        self.resource_name = resource_name
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        self.log_signal.emit("ActivationWorker not implemented yet.")
        self.finished_signal.emit()
