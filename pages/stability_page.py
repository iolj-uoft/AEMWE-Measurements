
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QFormLayout, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os
from plot_canvas import LivePlotCanvas
from worker.stability_worker import StabilityWorker

class StabilityPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Parameter fields
        self.interval_time_input = QLineEdit("60")
        self.input_current_input = QLineEdit("1.0")
        self.voltage_limit_input = QLineEdit("1.95")

        form_layout = QFormLayout()
        form_layout.addRow("Interval Time (s):", self.interval_time_input)
        form_layout.addRow("Input Current (A):", self.input_current_input)
        form_layout.addRow("Voltage Limit (V):", self.voltage_limit_input)

        # Horizontal layout: form on left, logo/author on right
        form_and_logo_layout = QHBoxLayout()
        form_and_logo_layout.addLayout(form_layout)

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

        self.start_button = QPushButton("Start Stability Test")
        self.start_button.clicked.connect(self.start_stability)
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
        self.stop_button.clicked.connect(self.stop_stability)
        layout.addWidget(self.stop_button)


        self.canvas = LivePlotCanvas()
        self.canvas.setMinimumHeight(450)
        layout.addWidget(self.canvas)

        # Export buttons
        from PyQt5.QtWidgets import QFileDialog
        self.export_plot_button = QPushButton("Export Plot")
        self.export_plot_button.clicked.connect(self.export_plot)
        layout.addWidget(self.export_plot_button)

        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_data_button)

        layout.addWidget(QLabel("Log"))

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.worker = None

    def log(self, msg):
        self.log_output.append(msg)

    def update_plot(self, x, y):
        # x: time (s), y: voltage (V)
        MAX_PLOT_POINTS = 1000  # Only plot the most recent 1000 points for performance
        if not hasattr(self, '_time_data'):
            self._time_data = []
            self._voltage_data = []
        self._time_data.append(x)
        self._voltage_data.append(y)
        # Only plot the last MAX_PLOT_POINTS points
        plot_time = self._time_data[-MAX_PLOT_POINTS:]
        plot_voltage = self._voltage_data[-MAX_PLOT_POINTS:]
        self.canvas.ax.clear()
        self.canvas.ax.set_title("Stability Test")
        self.canvas.ax.set_xlabel("Time (s)")
        self.canvas.ax.set_ylabel("Voltage")
        self.canvas.ax.set_ylim(0, 2)  # This sets the y-axis range fixed from 0 to 2
        self.canvas.ax.plot(plot_time, plot_voltage, marker='o', markersize=3, linestyle='-', color='blue')
        self.canvas.ax.grid(True)
        self.canvas.fig.tight_layout(pad=2.0)
        self.canvas.draw()

    def export_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Plot As", "stability_plot.png", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)", options=options)
        if file_path:
            self.canvas.fig.savefig(file_path)
            self.log(f"Plot exported to: {file_path}")

    def save_data(self):
        
        if not hasattr(self, '_time_data') or not self._time_data:
            QMessageBox.warning(self, "No Data", "No stability data to save.")
            return
        import pandas as pd
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Stability Data As", "stability_data.xlsx", "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)", options=options)
        if file_path:
            df = pd.DataFrame({"Time (s)": self._time_data, "Voltage": self._voltage_data})
            try:
                if file_path.endswith(".csv"):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                self.log(f"Stability data saved to: {file_path}")
            except Exception as e:
                self.log(f"Failed to save data: {str(e)}")

    def start_stability(self):
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

        interval_time = float(self.interval_time_input.text())
        input_current = float(self.input_current_input.text())
        voltage_limit = float(self.voltage_limit_input.text())

        # Reset plot data
        self._time_data = []
        self._voltage_data = []

        self.worker = StabilityWorker(selected_resource, interval_time, input_current, voltage_limit, output_folder)
        self.worker.log_signal.connect(self.log)
        self.worker.plot_signal.connect(self.update_plot)
        self.worker.finished_signal.connect(self.on_stability_finished)
        self.worker.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_stability(self):
        if self.worker:
            self.worker.stop()
            self.log("Stop requested. Waiting for shutdown...")
            self.stop_button.setEnabled(False)

    def on_stability_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log("Stability test completed.")
