from PyQt5.QtCore import QThread, pyqtSignal
import pyvisa
import time
from datetime import date
import pandas as pd


class MeasurementWorker(QThread):
    log_signal = pyqtSignal(str)
    plot_signal = pyqtSignal(float, float)
    finished_signal = pyqtSignal()
    request_user_input = pyqtSignal()

    def __init__(self, resource_name, activation_time, voltage_limit, interval_time, current_start=0.0, current_step=0.25):
        super().__init__()
        self.resource_name = resource_name
        self.activation_time = activation_time
        self.voltage_limit = voltage_limit
        self.interval_time = interval_time
        self.current_start = current_start
        self.current_step = current_step
        self.running = True
        self._wait_for_user = False

    def stop(self):
        self.running = False


    def run(self):
        try:
            rm = pyvisa.ResourceManager()
            pwr = rm.open_resource(self.resource_name)

            # Increase current until voltage limit is hit
            current = self.current_start

            self.log_signal.emit("Starting activation...")
            pwr.write('output on')
            pwr.write('CURR 1.0')
            time.sleep(self.activation_time)

            pwr.write('CURR 0.01')
            self.log_signal.emit("Waiting for user to confirm voltage stabilization...")
            self.request_user_input.emit()
            self._wait_for_user = True
            while self._wait_for_user:
                time.sleep(0.1)

            voltage_0 = float(pwr.query('MEASure:VOLTage?'))
            self.log_signal.emit(f'[{date.today()} {time.strftime("%H:%M:%S")}] {self.current_start:6.2f}A {voltage_0:7.3f}V')
            self.plot_signal.emit(self.current_start, voltage_0)



            voltage_data = [voltage_0]
            current_data = [self.current_start]

            while self.running:
                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                if measured_voltage >= self.voltage_limit:
                    self.log_signal.emit("Voltage limit exceeded. Shutting down.")
                    break

                current += self.current_step
                pwr.write(f'CURR {current}')
                time.sleep(self.interval_time)
                measured_voltage = float(pwr.query('MEASure:VOLTage?'))
                voltage_data.append(measured_voltage)
                current_data.append(current)
                self.log_signal.emit(f'[{date.today()} {time.strftime("%H:%M:%S")}] {current:6.2f}A {measured_voltage:7.3f}V')
                self.plot_signal.emit(current, measured_voltage)

            df = pd.DataFrame({'Current (A)': current_data, 'Voltage (V)': voltage_data})
            try:
                df.to_excel("output.xlsx", index=False)
                self.log_signal.emit("Data saved to output.xlsx")
            except PermissionError:
                self.log_signal.emit("Error saving Excel. Please close it and retry.")

            pwr.write('CURR 0')
            pwr.write('output off')
            pwr.close()

        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
        finally:
            self.finished_signal.emit()
