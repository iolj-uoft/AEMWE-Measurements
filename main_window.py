from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
import os
from pages.measurement_page import MeasurementPage
from pages.activation_page import ActivationPage
from pages.stability_page import StabilityPage

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEMWE Measurement Platform")
        self.setGeometry(100, 100, 900, 600)

        from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QFileDialog
        import pyvisa
        device_label = QLabel("Select VISA Device:")
        device_combo = QComboBox()
        try:
            device_combo.addItems(pyvisa.ResourceManager().list_resources())
        except Exception as e:
            device_combo.addItem("No VISA devices found")
        self.device_label = device_label
        self.device_combo = device_combo


        # User name input and display (replaces output folder selection)
        from PyQt5.QtWidgets import QLineEdit, QPushButton, QLabel
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("(Optional) Enter your name")
        self.username_input.setToolTip("Your name will be recorded with the measurement if provided")
        self.username_input.setMaximumWidth(140)
        self.username_btn = QPushButton("Set User")
        self.username_btn.clicked.connect(self.set_username)
        from PyQt5.QtCore import Qt
        self.username_display = QLabel("Current User: (none)")
        self.username_display.setAlignment(Qt.AlignCenter)
        self.username_display.setStyleSheet("color: #222; font-size: 15pt; font-weight: bold;")

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

        # Top layout for device selection and user name
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.device_label)
        top_layout.addWidget(self.device_combo)
        top_layout.addSpacing(30)
        top_layout.addWidget(self.username_input)
        top_layout.addWidget(self.username_btn)
        top_layout.addWidget(self.username_display)
        top_layout.addStretch()

        # Navigation and main content layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        content_layout = QHBoxLayout()
        content_layout.addLayout(nav_layout)
        content_layout.addWidget(self.stack)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
    def set_username(self):
        name = self.username_input.text().strip()
        if name:
            self.username_display.setText(f"Current User: {name}")
            self.username_input.hide()
            self.username_btn.hide()
        else:
            self.username_display.setText("Current User: (none)")
            self.username_input.show()
            self.username_btn.show()

    def get_selected_device(self):
        return self.device_combo.currentText()

    # Output folder selection removed; user name is now used instead
