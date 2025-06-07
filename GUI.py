import pyvisa
import time
from datetime import date
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class Worker(QThread):
    log_signal = pyqtSignal(str)
    plot_signal = pyqtSignal(float, float)
    finished_signal = pyqtSignal()

    def __init__(self, resource_name):
        super().__init__()
        self.resource_name = resource_name
        self.running = True

    def log(self, msg):
        self.log_signal.emit(msg)

    def run(self):
        try:
            rm = pyvisa.ResourceManager()
            pwr = rm.open_resource(self.resource_name)

            current_values = [0.25 + 1.25 * i for i in range(33)]
            voltage_limit = 1.95
            activation_time = 1
            interval_time = 20

            self.log("Starting activation...")
            pwr.write('output on')
            pwr.write('CURR 1.0')
            time.sleep(activation_time)

            self.log("Set current to 0.01A and wait for stabilization.")
            pwr.write('CURR 0.01')
            input("Please press Enter in the console after voltage stabilizes...")
            voltage_0 = float(pwr.query('MEASure:VOLTage?'))
            self.log(f'{date.today()} {time.strftime("%H:%M:%S")} - 0A {voltage_0:.3f}V')
            self.plot_signal.emit(0.0, voltage_0)

            voltage_data = [voltage_0]
            current_data = [0.0]

            for curr in current_values:
                if not self.running:
                    self.log("⚠️ Measurement stopped by user.")
                    break

                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                if measured_voltage >= voltage_limit:
                    self.log("Voltage limit exceeded. Shutting down.")
                    pwr.write('CURR 0')
                    break

                pwr.write(f'CURR {curr}')
                time.sleep(interval_time)
                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                voltage_data.append(measured_voltage)
                current_data.append(curr)

                self.log(f'{date.today()} {time.strftime("%H:%M:%S")} - {curr}A {measured_voltage:.3f}V')
                self.plot_signal.emit(curr, measured_voltage)

            df = pd.DataFrame({'Current (A)': current_data, 'Voltage (V)': voltage_data})
            try:
                df.to_excel("output.xlsx", index=False)
                self.log("Data saved to output.xlsx")
            except PermissionError:
                self.log("❌ Error saving Excel. Please close it and retry.")

            pwr.write('CURR 0')
            pwr.write('output off')
            pwr.close()
        except Exception as e:
            self.log(f"⚠️ Error: {e}")
        finally:
            self.finished_signal.emit()
            
    def stop(self):
        self.running = False

class LivePlotCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 3))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Polarization Curve")
        self.ax.set_xlabel("Current Density (mA/cm²)")
        self.ax.set_ylabel("Voltage (V)")
        self.x_data = []
        self.y_data = []
        super().__init__(self.fig)

    def update_plot(self, x, y):
        self.x_data.append(x)
        self.y_data.append(y)
        self.ax.clear()
        self.ax.set_title("Polarization Curve")
        self.ax.set_xlabel("Current Density (mA/cm²)")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.plot(self.x_data, self.y_data, marker='o', linestyle='-')
        self.draw()


class MeasurementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Power Supply Measurement with Live Plot")
        self.setGeometry(200, 200, 700, 600)
        self.worker = None

        layout = QVBoxLayout()

        self.label = QLabel("Select VISA Device:")
        layout.addWidget(self.label)

        self.combo = QComboBox()
        self.combo.addItems(pyvisa.ResourceManager().list_resources())
        layout.addWidget(self.combo)

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
        self.worker.log_signal.connect(self.append_log)
        self.worker.plot_signal.connect(self.update_plot)
        self.worker.finished_signal.connect(self.on_measurement_finished)
        self.worker.start()

    def on_measurement_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.append_log("Measurement completed.")

    def stop_measurement(self):
        if self.worker:
            self.worker.stop()
            self.append_log("🟥 Stop requested. Waiting for shutdown...")
            self.stop_button.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MeasurementApp()
    window.show()
    sys.exit(app.exec_())
