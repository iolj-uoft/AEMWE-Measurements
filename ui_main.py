from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QMessageBox, QInputDialog, QLineEdit, QFormLayout, QHBoxLayout
import pyvisa
from worker import Worker
from plot_canvas import LivePlotCanvas

class MeasurementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Power Supply Measurement")
        self.setGeometry(200, 200, 700, 600)
        self.worker = None

        layout = QVBoxLayout()

        self.label = QLabel("Select VISA Device:")
        layout.addWidget(self.label)

        self.combo = QComboBox()
        self.combo.addItems(pyvisa.ResourceManager().list_resources())
        layout.addWidget(self.combo)

        # Parameter fields
        self.activation_time_input = QLineEdit("60")  # default values
        self.voltage_limit_input = QLineEdit("1.95")
        self.interval_time_input = QLineEdit("20")

        form_layout = QFormLayout()
        form_layout.addRow("Activation Time (s):", self.activation_time_input)
        form_layout.addRow("Voltage Limit (V):", self.voltage_limit_input)
        form_layout.addRow("Interval Time (s):", self.interval_time_input)
        layout.addLayout(form_layout)

        self.start_button = QPushButton("Start Measurement")
        self.start_button.clicked.connect(self.start_measurement)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_measurement)
        layout.addWidget(self.stop_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.canvas = LivePlotCanvas()
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def append_log(self, text):
        self.log_output.append(text)

    def update_plot(self, x, y):
        self.canvas.update_plot(x, y)

    def start_measurement(self):
        selected_resource = self.combo.currentText()
        if not selected_resource:
            QMessageBox.warning(self, "Warning", "Please select a VISA device.")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.canvas.x_data.clear()
        self.canvas.y_data.clear()
        self.canvas.ax.clear()

        self.worker = Worker(selected_resource)
        self.worker.request_user_input.connect(self.prompt_user_to_continue)
        self.worker.log_signal.connect(self.append_log)
        self.worker.plot_signal.connect(self.update_plot)
        self.worker.finished_signal.connect(self.on_measurement_finished)
        self.worker.start()

    def stop_measurement(self):
        if self.worker:
            self.worker.stop()
            self.append_log("🟥 Stop requested. Waiting for shutdown...")
            self.stop_button.setEnabled(False)
            
    def prompt_user_to_continue(self):
        QInputDialog.getText(self, "Stabilization", "Press OK when voltage stabilizes.")
        if self.worker:
            self.worker._wait_for_user = False


    def on_measurement_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.append_log("✅ Measurement completed.")
