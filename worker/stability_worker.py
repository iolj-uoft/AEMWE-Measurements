from PyQt5.QtCore import QThread, pyqtSignal
import pyvisa
import time
from datetime import datetime
import pandas as pd
import os

class StabilityWorker(QThread):
    log_signal = pyqtSignal(str)
    plot_signal = pyqtSignal(float, float)
    finished_signal = pyqtSignal()

    def __init__(self, resource_name, interval_time, input_current, voltage_limit, output_folder):
        super().__init__()
        self.resource_name = resource_name
        self.interval_time = interval_time
        self.input_current = input_current
        self.voltage_limit = voltage_limit
        self.output_folder = output_folder
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        try:
            rm = pyvisa.ResourceManager()
            pwr = rm.open_resource(self.resource_name)
            pwr.write('output on')
            pwr.write(f'CURR {self.input_current}')
            self.log_signal.emit(f"Stability test started at {self.input_current}A.")
            start_time = datetime.now()
            time_data = []
            voltage_data = []
            save_interval = 50
            while self.running:
                elapsed = (datetime.now() - start_time).total_seconds()
                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                time_data.append(elapsed)
                voltage_data.append(measured_voltage)
                # Log format: [YYYY-MM-DD HH:MM:SS] t=xx.xs, V=yy.yyyV
                self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {measured_voltage:7.3f}V")
                self.plot_signal.emit(elapsed, measured_voltage)
                # Save every 50 points
                if len(time_data) % save_interval == 0:
                    self._save_data(time_data, voltage_data)
                if measured_voltage >= self.voltage_limit:
                    self.log_signal.emit("Voltage limit exceeded. Stopping test.")
                    break
                for _ in range(int(self.interval_time * 10)):
                    if not self.running:
                        break
                    time.sleep(0.1)
                if not self.running:
                    self.log_signal.emit("Stability test stopped by user.")
                    break
            # Final save
            self._save_data(time_data, voltage_data)
            pwr.write('output off')
            pwr.close()
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
        finally:
            self.finished_signal.emit()

    def _save_data(self, time_data, voltage_data):
        output_path = os.path.join(self.output_folder, "stability_output.xlsx")
        try:
            df = pd.DataFrame({'Time (s)': time_data, 'Voltage (V)': voltage_data})
            df.to_excel(output_path, index=False)
            self.log_signal.emit(f"Data saved to {output_path}")
        except PermissionError:
            self.log_signal.emit("Error saving Excel. Please close it and retry.")
