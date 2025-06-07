from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy

class LivePlotCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Polarization Curve")
        self.ax.set_xlabel("Current Density(mA/cm²)")
        self.ax.set_ylabel("Voltage (V)")
        self.x_data = []
        self.y_data = []
        self.ax.grid(True)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def update_plot(self, x, y):
        self.x_data.append(x)
        self.y_data.append(y)
        self.ax.clear()
        self.ax.set_title("Polarization Curve")
        self.ax.set_xlabel("Current Density(mA/cm²)")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.plot([x * 40 for x in self.x_data], self.y_data, marker='o', markersize='3', linestyle='-', color='blue')
        self.ax.grid(True)
        if self.y_data:
            y_min = min(self.y_data)
            y_max = max(self.y_data)
            y_range = y_max - y_min
            self.ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range if y_range > 0 else y_max + 0.2)

        self.fig.tight_layout(pad=2.0)
        self.draw()

