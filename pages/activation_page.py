from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QFormLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os
from worker.activation_worker import ActivationWorker

class ActivationPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Parameter fields
        self.activation_time_input = QLineEdit("60")
        self.voltage_limit_input = QLineEdit("1.95")
        self.num_cycles_input = QLineEdit("30")
        self.interval_time_input = QLineEdit("60")

        form_layout = QFormLayout()
        form_layout.addRow("Activation Time (s):", self.activation_time_input)
        form_layout.addRow("Voltage Limit (V):", self.voltage_limit_input)
        form_layout.addRow("Number of Cycles:", self.num_cycles_input)
        form_layout.addRow("Interval Time (s):", self.interval_time_input)

        # Horizontal layout: form on left, logo/author on right (copied from measurement page)
        form_and_logo_layout = QHBoxLayout()
        form_and_logo_layout.addLayout(form_layout)

        # Logo + author layout (right side)
        logo_and_author_layout = QVBoxLayout()
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "../assets/logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaledToHeight(80, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_and_author_layout.addWidget(logo_label)

        author_label = QLabel("Author: Yang-Chen Lin\nContact: yangchen.lin0524@gmail.com\nLicensed under MIT License\nCopyright (c) 2025")
        author_label.setAlignment(Qt.AlignCenter)
        logo_and_author_layout.addWidget(author_label)
        logo_and_author_layout.addStretch()

        form_and_logo_layout.addLayout(logo_and_author_layout)
        layout.addLayout(form_and_logo_layout)

        self.start_button = QPushButton("Start Activation")
        self.start_button.clicked.connect(self.start_activation)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f28b82;
                border: 1px solid #d14836;
                color: black;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #f2f2f2;
                color: gray;
                border: 1px solid #ccc;
            }
        """)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_activation)
        layout.addWidget(self.stop_button)

        # Add plot area (copied from measurement page)
        from plot_canvas import LivePlotCanvas
        self.canvas = LivePlotCanvas()
        self.canvas.setMinimumHeight(450)
        layout.addWidget(self.canvas)

        layout.addWidget(QLabel("Activation Mode"))

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.worker = None
        self.voltage_data = []

    def log(self, msg):
        self.log_output.append(msg)

    def update_plot(self, x, y):
        self.canvas.update_plot(x, y)
        self.voltage_data.append([y])

    def start_activation(self):
        main_window = self.window()
        if hasattr(main_window, 'get_selected_device') and hasattr(main_window, 'get_output_folder'):
            selected_resource = main_window.get_selected_device()
            output_folder = main_window.get_output_folder()
        else:
            selected_resource = None
            output_folder = "."
        if not selected_resource or "No VISA devices found" in selected_resource:
            QMessageBox.warning(self, "Warning", "Please select a VISA device.")
            return

        activation_time = float(self.activation_time_input.text())
        voltage_limit = float(self.voltage_limit_input.text())
        num_cycles = int(self.num_cycles_input.text())
        interval_time = float(self.interval_time_input.text())

        self.worker = ActivationWorker(selected_resource, activation_time, voltage_limit, num_cycles, interval_time, output_folder)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_activation_finished)
        self.worker.request_user_input.connect(self.prompt_user_to_continue)
        # Connect plot signal if implemented in worker
        if hasattr(self.worker, 'plot_signal'):
            self.worker.plot_signal.connect(self.update_plot)
        self.worker.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_activation(self):
        if self.worker:
            self.worker.stop()
            self.log("Stop requested. Waiting for shutdown...")
            self.stop_button.setEnabled(False)

    def prompt_user_to_continue(self):
        QMessageBox.information(self, "Stabilization", "Press OK when voltage stabilizes.")
        if self.worker:
            self.worker._wait_for_user = False

    def on_activation_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log("Activation completed.")
