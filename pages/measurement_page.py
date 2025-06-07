
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QMessageBox, QInputDialog, QLineEdit, QFormLayout
import pyvisa
from plot_canvas import LivePlotCanvas
import sys
import os
from worker.measurement_worker import MeasurementWorker

class MeasurementPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Power Supply Measurement")
        self.setGeometry(200, 200, 700, 600)
        self.worker = None

        layout = QVBoxLayout()

        self.label = QLabel("Select VISA Device:")
        layout.addWidget(self.label)

        self.combo = QComboBox()
        try:
            self.combo.addItems(pyvisa.ResourceManager().list_resources())
        except Exception as e:
            self.combo.addItem("No VISA devices found")
        layout.addWidget(self.combo)


        # Parameter fields
        self.activation_time_input = QLineEdit("60")  # default values
        self.voltage_limit_input = QLineEdit("1.95")
        self.interval_time_input = QLineEdit("20")


        self.current_start_input = QLineEdit("0.0")
        self.current_step_input = QLineEdit("0.25")

        form_layout = QFormLayout()
        form_layout.addRow("Activation Time (s):", self.activation_time_input)
        form_layout.addRow("Voltage Limit (V):", self.voltage_limit_input)
        form_layout.addRow("Interval Time (s):", self.interval_time_input)
        form_layout.addRow("Start Current (A):", self.current_start_input)
        form_layout.addRow("Current Step (A):", self.current_step_input)
        layout.addLayout(form_layout)

        self.start_button = QPushButton("Start Measurement")
        self.start_button.clicked.connect(self.start_measurement)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_measurement)
        layout.addWidget(self.stop_button)


        self.canvas = LivePlotCanvas()
        layout.addWidget(self.canvas)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def append_log(self, text):
        self.log_output.append(text)

    def update_plot(self, x, y):
        self.canvas.update_plot(x, y)

    def start_measurement(self):
        selected_resource = self.combo.currentText()
        if not selected_resource or "No VISA devices found" in selected_resource:
            QMessageBox.warning(self, "Warning", "Please select a VISA device.")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.canvas.x_data.clear()
        self.canvas.y_data.clear()
        self.canvas.ax.clear()

        activation_time = float(self.activation_time_input.text())
        voltage_limit = float(self.voltage_limit_input.text())
        interval_time = float(self.interval_time_input.text())
        current_start = float(self.current_start_input.text())
        current_step = float(self.current_step_input.text())
        
        self.worker = MeasurementWorker(selected_resource, activation_time, voltage_limit, interval_time, current_start, current_step)
        self.worker.request_user_input.connect(self.prompt_user_to_continue)
        self.worker.log_signal.connect(self.append_log)
        self.worker.plot_signal.connect(self.update_plot)
        self.worker.finished_signal.connect(self.on_measurement_finished)
        self.worker.start()

    def stop_measurement(self):
        if self.worker:
            self.worker.stop()
            self.append_log("Stop requested. Waiting for shutdown...")
            self.stop_button.setEnabled(False)

    def prompt_user_to_continue(self):
        QInputDialog.getText(self, "Stabilization", "Press OK when voltage stabilizes.")
        if self.worker:
            self.worker._wait_for_user = False

    def on_measurement_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.append_log("Measurement completed.")
