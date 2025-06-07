from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class LivePlotCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 3))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Voltage vs Current")
        self.ax.set_xlabel("Current (A)")
        self.ax.set_ylabel("Voltage (V)")
        self.x_data = []
        self.y_data = []
        super().__init__(self.fig)

    def update_plot(self, x, y):
        self.x_data.append(x)
        self.y_data.append(y)
        self.ax.clear()
        self.ax.set_title("Voltage vs Current")
        self.ax.set_xlabel("Current (A)")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.plot(self.x_data, self.y_data, marker='o', linestyle='-')
        if self.y_data:
            y_min = min(self.y_data)
            y_max = max(self.y_data)
            y_range = y_max - y_min
            # Add 10% padding above and below
            self.ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range if y_range > 0 else y_max + 0.2)
        self.draw()
