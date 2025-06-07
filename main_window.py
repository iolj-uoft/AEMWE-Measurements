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

        # Output folder selection
        self.output_folder = os.getcwd()
        self.output_folder_label = QLabel(f"Output Folder: {self.output_folder}")
        self.select_folder_btn = QPushButton("Select Output Folder")
        self.select_folder_btn.clicked.connect(self.select_output_folder)

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

        # Top layout for device selection and output folder
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.device_label)
        top_layout.addWidget(self.device_combo)
        top_layout.addSpacing(30)
        top_layout.addWidget(self.output_folder_label)
        top_layout.addWidget(self.select_folder_btn)
        top_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        content_layout = QHBoxLayout()
        content_layout.addLayout(nav_layout)
        content_layout.addWidget(self.stack)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def get_selected_device(self):
        return self.device_combo.currentText()

    def get_output_folder(self):
        return self.output_folder

    def select_output_folder(self):
        from PyQt5.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_folder)
        if folder:
            self.output_folder = folder
            self.output_folder_label.setText(f"Output Folder: {self.output_folder}")
