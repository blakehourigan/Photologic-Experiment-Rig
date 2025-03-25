import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk


class RasterizedDataWindow(tk.Toplevel):
    def __init__(self, side, exp_data) -> None:
        super().__init__()
        self.exp_data = exp_data
        self.event_data = self.exp_data.event_data

        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        self.bind("<Control-w>", lambda e: self.withdraw())

        self.title(f"Side {side} Lick Time Raster Plot")

        # Initialize the color cycle
        self.color_cycle = cm.get_cmap("tab10", 10)

        # Initialize the color index
        self.color_index = 0

        self.withdraw()

    def show(self):
        self.deiconify()

    def create_plot(self) -> None:
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        fig, axes = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, container)

        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, container)
        toolbar.update()

        num_trials = self.exp_data.exp_var_entries["Num Trials"]

        axes.set_xlim(0, 21)
        axes.set_ylim(0, num_trials + 1)

        self.canvas = canvas
        self.axes = axes

    def update_plot(
        self,
        lick_times=None,
        logical_trial=None,
    ) -> None:
        axes = self.axes
        canvas = self.canvas

        self.color_index = (self.color_index + 1) % 10

        if lick_times and len(lick_times) > 0:
            color = [self.color_cycle(self.color_index)]

            # x values for this trial
            lick_times = [stamp - lick_times[0] for stamp in lick_times]

            # we need a y for each x value (lick timestamp)
            y_values = [logical_trial] * len(lick_times)

            axes.scatter(lick_times, y_values, marker="|", c=color, s=100)

        canvas.draw()
