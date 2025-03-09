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

        self.create_plot(self, side)
        self.update_plot(self)

        self.withdraw()

    def show(self):
        self.deiconify()

    def create_plot(self, window: tk.Toplevel, side: int) -> None:
        container = tk.Frame(window)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        fig, axes = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, container)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, container)
        toolbar.update()

        window.canvas = canvas
        window.axes = axes

        sd1_len = len(self.event_data.side_one_trial_licks)
        sd2_len = len(self.event_data.side_one_trial_licks) > 0

        if sd1_len > 0 or sd2_len:
            # Pass the whole window to update_plot
            self.update_plot(window, reopen=True, side=side)
        else:
            self.update_plot(window)

    def update_plot(
        self,
        window: tk.Toplevel,
        lick_times=None,
        trial_index=None,
        reopen=False,
        side=0,
    ):
        axes = window.axes
        canvas = window.canvas

        num_trials = self.exp_data.exp_var_entries["Num Trials"]

        axes.set_xlim(0, 21)
        axes.set_ylim(0, num_trials + 1)

        self.color_index = (self.color_index + 1) % 10

        if lick_times and len(lick_times) > 0:
            color = self.color_cycle(self.color_index)
            lick_times = [stamp - lick_times[0] for stamp in lick_times]
            axes.scatter(
                lick_times, [trial_index] * len(lick_times), marker="|", c=color, s=100
            )
            self.color_index = (self.color_index + 1) % 10

        canvas.draw()

    def plot_licks(self, axes, lick_times, trial_index, color):
        # Normalize lick times by the first lick time
        normalized_licks = [stamp - lick_times[0] for stamp in lick_times]
        axes.scatter(
            normalized_licks,
            [trial_index] * len(normalized_licks),
            marker="|",
            c=color,
            s=100,
        )
