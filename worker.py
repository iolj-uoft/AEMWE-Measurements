from PyQt5.QtCore import QThread, pyqtSignal
import pyvisa
import time
from datetime import date
import pandas as pd

class Worker(QThread):
    log_signal = pyqtSignal(str)
    plot_signal = pyqtSignal(float, float)
    finished_signal = pyqtSignal()
    request_user_input = pyqtSignal()

    def __init__(self, resource_name, activation_time, voltage_limit, interval_time):
        super().__init__()
        self.resource_name = resource_name
        self.activation_time = activation_time
        self.voltage_limit = voltage_limit
        self.interval_time = interval_time
        self.running = True
        self._wait_for_user = False  # Also initialize this here


    def stop(self):
        self.running = False

    def run(self):
        try:
            rm = pyvisa.ResourceManager()
            pwr = rm.open_resource(self.resource_name)

            current_values = [0.25 + 1.25 * i for i in range(33)]
            voltage_limit = 1.95
            activation_time = 1
            interval_time = 1

            self.log_signal.emit("Starting activation...")
            pwr.write('output on')
            pwr.write('CURR 1.0')
            time.sleep(activation_time)

            pwr.write('CURR 0.01')
            self.log_signal.emit("Waiting for user to confirm voltage stabilization...")
            self.request_user_input.emit() 
            self._wait_for_user = True
            while self._wait_for_user:
                time.sleep(0.1)  # block the worker thread until GUI responds
            voltage_0 = float(pwr.query('MEASure:VOLTage?'))
            self.log_signal.emit(f'{date.today()} {time.strftime("%H:%M:%S")} - 0A {voltage_0:.3f}V')
            self.plot_signal.emit(0.0, voltage_0)

            voltage_data = [voltage_0]
            current_data = [0.0]

            for curr in current_values:
                if not self.running:
                    self.log_signal.emit("⚠️ Measurement stopped by user.")
                    break

                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                if measured_voltage >= voltage_limit:
                    self.log_signal.emit("Voltage limit exceeded. Shutting down.")
                    break

                pwr.write(f'CURR {curr}')
                time.sleep(interval_time)
                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                voltage_data.append(measured_voltage)
                current_data.append(curr)
                self.log_signal.emit(f'{date.today()} {time.strftime("%H:%M:%S")} - {curr}A {measured_voltage:.3f}V')
                self.plot_signal.emit(curr, measured_voltage)

            df = pd.DataFrame({'Current (A)': current_data, 'Voltage (V)': voltage_data})
            try:
                df.to_excel("output.xlsx", index=False)
                self.log_signal.emit("Data saved to output.xlsx")
            except PermissionError:
                self.log_signal.emit("❌ Error saving Excel. Please close it and retry.")

            pwr.write('CURR 0')
            pwr.write('output off')
            pwr.close()
        except Exception as e:
            self.log_signal.emit(f"⚠️ Error: {e}")
        finally:
            self.finished_signal.emit()
