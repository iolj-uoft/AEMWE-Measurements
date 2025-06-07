from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QMessageBox, QInputDialog, QLineEdit, QFormLayout, QFileDialog, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import pyvisa
import os
import pandas as pd
from plot_canvas import LivePlotCanvas
from worker.measurement_worker import MeasurementWorker

class MeasurementPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Power Supply Measurement")
        self.setGeometry(200, 200, 700, 600)
        self.worker = None
        self.voltage_data = []

        layout = QVBoxLayout()

        # Parameter fields
        self.activation_time_input = QLineEdit("60")
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

        # Horizontal layout: form on left, logo/author on right
        form_and_logo_layout = QHBoxLayout()
        form_and_logo_layout.addLayout(form_layout)

        # Logo + author layout (right side)
        logo_and_author_layout = QVBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), "../assets/logo.png"))
        logo_label.setPixmap(logo_pixmap.scaledToHeight(80, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_and_author_layout.addWidget(logo_label)

        author_label = QLabel("Author: Yang-Chen Lin\nContact: yangchen.lin0524@gmail.com\nLicensed under MIT License\nCopyright (c) 2025")
        author_label.setAlignment(Qt.AlignCenter)
        logo_and_author_layout.addWidget(author_label)
        logo_and_author_layout.addStretch()

        form_and_logo_layout.addLayout(logo_and_author_layout)
        layout.addLayout(form_and_logo_layout)

        self.start_button = QPushButton("Start Measurement")
        self.start_button.clicked.connect(self.start_measurement)
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
        self.stop_button.clicked.connect(self.stop_measurement)
        layout.addWidget(self.stop_button)

        self.canvas = LivePlotCanvas()
        self.canvas.setMinimumHeight(450)
        layout.addWidget(self.canvas)

        self.export_plot_button = QPushButton("Export Plot")
        self.export_plot_button.clicked.connect(self.export_plot)
        layout.addWidget(self.export_plot_button)

        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_data_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def export_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Plot As", "plot.png", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)", options=options)
        if file_path:
            self.canvas.fig.savefig(file_path)
            self.append_log(f"Plot exported to: {file_path}")

    def save_data(self):
        if not self.voltage_data:
            QMessageBox.warning(self, "No Data", "No voltage data to save.")
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Voltage Data As", "voltage_data.xlsx", "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)", options=options)

        if file_path:
            df = pd.DataFrame(self.voltage_data, columns=["Voltage (V)"])
            try:
                if file_path.endswith(".csv"):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                self.append_log(f"✅ Voltage data saved to: {file_path}")
            except Exception as e:
                self.append_log(f"❌ Failed to save data: {str(e)}")

    def append_log(self, text):
        self.log_output.append(text)

    def update_plot(self, x, y):
        self.canvas.update_plot(x, y)
        self.voltage_data.append([y])

    def start_measurement(self):
        # Get selected device from parent MainWindow
        main_window = self.window()
        if hasattr(main_window, 'get_selected_device'):
            selected_resource = main_window.get_selected_device()
        else:
            selected_resource = None
        if not selected_resource or "No VISA devices found" in selected_resource:
            QMessageBox.warning(self, "Warning", "Please select a VISA device.")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.canvas.x_data.clear()
        self.canvas.y_data.clear()
        self.canvas.ax.clear()
        self.voltage_data.clear()

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
        msg = QMessageBox(self)
        msg.setWindowTitle("Stabilization")
        msg.setText("Press OK when voltage stabilizes.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        if self.worker:
            self.worker._wait_for_user = False

    def on_measurement_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.append_log("Measurement completed.")
