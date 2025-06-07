from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

class StabilityPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        layout.addWidget(QLabel("Stability Test Mode"))
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def log(self, msg):
        self.log_output.append(msg)
