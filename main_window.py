from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from pages.measurement_page import MeasurementPage
from pages.activation_page import ActivationPage
from pages.stability_page import StabilityPage

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEMWE Measurement Platform")
        self.setGeometry(100, 100, 900, 600)

        self.stack = QStackedWidget()
        self.measurement_page = MeasurementPage()
        self.activation_page = ActivationPage()
        self.stability_page = StabilityPage()

        self.stack.addWidget(self.measurement_page)
        self.stack.addWidget(self.activation_page)
        self.stack.addWidget(self.stability_page)

        self.measurement_btn = QPushButton("Measurement")
        self.measurement_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.measurement_page))

        self.activation_btn = QPushButton("Activation")
        self.activation_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.activation_page))

        self.stability_btn = QPushButton("Stability Test")
        self.stability_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.stability_page))

        nav_layout = QVBoxLayout()
        nav_layout.addWidget(self.measurement_btn)
        nav_layout.addWidget(self.activation_btn)
        nav_layout.addWidget(self.stability_btn)
        nav_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.stack)

        self.setLayout(main_layout)
