from PyQt5.QtCore import QThread, pyqtSignal
import pyvisa
import time
from datetime import date
import pandas as pd
import numpy as np
import os

class ActivationWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    request_user_input = pyqtSignal()
    plot_signal = pyqtSignal(float, float)

    def __init__(self, resource_name, activation_time, voltage_limit, num_cycles, interval_time, output_folder):
        super().__init__()
        self.resource_name = resource_name
        self.activation_time = activation_time
        self.voltage_limit = voltage_limit
        self.num_cycles = num_cycles
        self.interval_time = interval_time
        self.output_folder = output_folder
        self.running = True
        self._wait_for_user = False

    def stop(self):
        self.running = False

    def run(self):
        try:
            rm = pyvisa.ResourceManager()
            pwr = rm.open_resource(self.resource_name)
            self.log_signal.emit("Starting activation cycles...")
            pwr.write('output on')
            for i in range(self.num_cycles):
                if not self.running:
                    self.log_signal.emit("Activation stopped by user.")
                    break
                self.log_signal.emit(f"Cycle {i+1}/{self.num_cycles}: 1A Activating...")
                pwr.write('CURR 1.0')
                time.sleep(self.activation_time)
                self.log_signal.emit(f"Cycle {i+1}/{self.num_cycles}: 10A Activating...")
                pwr.write('CURR 10.0')
                time.sleep(self.activation_time)

            # Current sweep

            current_list = []
            voltage_list = []
            pwr.write('CURR 0.01')
            self.log_signal.emit("Waiting for user to confirm voltage stabilization...")
            self.request_user_input.emit()
            self._wait_for_user = True
            while self._wait_for_user:
                time.sleep(0.1)
            voltage_0 = float(pwr.query('MEASure:VOLTage?'))
            voltage_list.append(voltage_0)
            current_list.append(0.0)
            self.log_signal.emit(f'[{date.today()} {time.strftime("%H:%M:%S")}] {0:6.2f}A {voltage_0:7.3f}V')
            self.plot_signal.emit(0.0, voltage_0)

            current_sweep = np.arange(0.25, 40.25, 0.25)
            for curr in current_sweep:
                if not self.running:
                    self.log_signal.emit("Activation stopped by user.")
                    break
                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                if measured_voltage >= self.voltage_limit:
                    self.log_signal.emit("Voltage limit exceeded. Shutting down.")
                    pwr.write('CURR 0')
                    pwr.write('output off')
                    break
                pwr.write(f'CURR {curr}')
                time.sleep(self.interval_time)
                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                voltage_list.append(measured_voltage)
                current_list.append(curr)
                self.log_signal.emit(f'[{date.today()} {time.strftime("%H:%M:%S")}] {curr:6.2f}A {measured_voltage:7.3f}V')
                self.plot_signal.emit(curr, measured_voltage)

            # Save data (ensure same length)
            min_len = min(len(current_list), len(voltage_list))
            df = pd.DataFrame({'Current (A)': current_list[:min_len], 'Voltage (V)': voltage_list[:min_len]})
            output_path = os.path.join(self.output_folder, "activation_output.xlsx")
            try:
                df.to_excel(output_path, index=False)
                self.log_signal.emit(f"Data saved to {output_path}")
            except PermissionError:
                self.log_signal.emit("Error saving Excel. Please close it and retry.")

            pwr.write('CURR 0')
            pwr.write('output off')
            pwr.close()
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
        finally:
            self.finished_signal.emit()
