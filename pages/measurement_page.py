from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QMessageBox, QInputDialog, QLineEdit, QFormLayout, QFileDialog, QHBoxLayout
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

        self.current_list_input = QLineEdit("")
        self.import_current_btn = QPushButton("Import")
        self.import_current_btn.setToolTip("Import current list from CSV or text file")
        self.import_current_btn.clicked.connect(self.import_current_list)

        # Horizontal layout for current list input and import button
        current_list_hbox = QHBoxLayout()
        current_list_hbox.addWidget(self.current_list_input)
        current_list_hbox.addWidget(self.import_current_btn)

        # Label to display parsed current list below the input
        from PyQt5.QtWidgets import QScrollArea
        self.current_list_display = QLabel()
        self.current_list_display.setWordWrap(True)
        self.current_list_display.setStyleSheet("color: #333; font-size: 11pt; background: #f7f7f7; border: 1px solid #ddd; padding: 4px;")
        self.current_list_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # Put the label in a scroll area
        self.current_list_scroll = QScrollArea()
        self.current_list_scroll.setWidgetResizable(True)
        self.current_list_scroll.setWidget(self.current_list_display)
        self.current_list_scroll.setFixedHeight(70)

        form_layout = QFormLayout()
        form_layout.addRow("Activation Time (s):", self.activation_time_input)
        form_layout.addRow("Voltage Limit (V):", self.voltage_limit_input)
        form_layout.addRow("Interval Time (s):", self.interval_time_input)
        form_layout.addRow("Current List (comma/space separated or import):", current_list_hbox)
        form_layout.addRow("Current List (A):", self.current_list_scroll)

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

    def set_username(self):
        name = self.username_input.text().strip()
        if name:
            self.username_display.setText(f"Current User: {name}")
            self.username_input.hide()
            self.username_btn.hide()
        else:
            self.username_display.setText("Current User: (none)")


    def import_current_list(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Current List",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        if not file_path:
            return
        try:
            import csv
            numbers = []
            with open(file_path, 'r') as f:
                # Try CSV reader first for robust parsing
                try:
                    reader = csv.reader(f)
                    for row in reader:
                        for item in row:
                            for val in str(item).replace(',', ' ').split():
                                if val.strip():
                                    numbers.append(val.strip())
                except Exception:
                    f.seek(0)
                    content = f.read()
                    content = content.replace('\n', ' ').replace(',', ' ')
                    numbers = [s for s in content.split() if s.strip()]
            floats = []
            for s in numbers:
                try:
                    floats.append(str(float(s)))
                except Exception:
                    continue
            if not floats:
                QMessageBox.warning(self, "Import Error", "No valid numbers found in file.")
                return
            self.current_list_input.setText(' '.join(floats))
            self.update_current_list_display()
            self.append_log(f"✅ Imported {len(floats)} current values from file.")
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import current list: {str(e)}")
            self.append_log(f"❌ Failed to import current list: {str(e)}")

    def update_current_list_display(self):
        current_list_str = self.current_list_input.text().strip()
        # Show default list if no custom list, otherwise show only custom list
        try:
            default_list = [round(0 + i * 0.25, 8) for i in range(int((40 - 0) / 0.25) + 1)]
            default_str = ', '.join(f"{v:g}" for v in default_list)
            default_html = f"<b>Default:</b> {default_str}"
        except Exception:
            default_html = "<i>No default list available.</i>"

        if not current_list_str:
            self.current_list_display.setText(default_html)
            return
        try:
            # Accept comma, space, or newline separated
            current_list_str = current_list_str.replace('\n', ' ').replace(',', ' ')
            floats = [float(s) for s in current_list_str.split() if s.strip()]
            if not floats:
                self.current_list_display.setText("<i>No valid numbers in custom list.</i>")
            else:
                display_str = ', '.join(f"{v:g}" for v in floats)
                self.current_list_display.setText(display_str)
        except Exception:
            self.current_list_display.setText("<i>Invalid custom list input.</i>")
    def showEvent(self, event):
        super().showEvent(event)
        self.update_current_list_display()

    def on_current_list_input_changed(self):
        self.update_current_list_display()

        # Connect current list input changes to update display
        self.current_list_input.textChanged.connect(self.on_current_list_input_changed)

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

        current_list_str = self.current_list_input.text().strip()
        current_list = None
        if current_list_str:
            try:
                current_list_str = current_list_str.replace('\n', ' ').replace(',', ' ')
                current_list = [float(s) for s in current_list_str.split() if s.strip()]
            except Exception as e:
                QMessageBox.warning(self, "Invalid Current List", f"Could not parse current list: {str(e)}")
                return

        self.worker = MeasurementWorker(selected_resource, activation_time, voltage_limit, interval_time, current_start, current_step, current_list)
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
