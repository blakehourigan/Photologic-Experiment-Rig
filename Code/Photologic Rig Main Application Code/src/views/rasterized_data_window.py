import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk


class RasterizedDataWindow(tk.Toplevel):
    def __init__(self, side) -> None:
        super().__init__()

        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        self.bind("<Control-w>", lambda e: self.withdraw())
        self.iconbitmap(self.master.iconbitmap())  # Assuming master has a set icon
        self.title(f"Side {side} Raster Plot")

        # Initialize the color cycle
        self.color_cycle = cm.get_cmap("tab10", 10)
        # Initialize the color index
        self.color_index = 0

        self.withdraw()

    def create_plot(self, window: tk.Toplevel, side: int) -> None:
        container = tk.Frame(window)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        fig, axes = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, container)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, container)
        toolbar.update()

        window.canvas = canvas  # type: ignore
        window.axes = axes  # type: ignore

        if (
            len(self.controller.data_mgr.side_one_trial_licks) > 0
            or len(self.controller.data_mgr.side_one_trial_licks) > 0
        ):
            self.update_plot(
                window, reopen=True, side=side
            )  # Pass the whole window to update_plot
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
        axes = window.axes  # type: ignore
        canvas = window.canvas  # type: ignore

        axes.set_xlim(0, 21)
        axes.set_ylim(0, self.controller.get_num_trials() + 1)

        # Handle the re-open scenario by plotting all previous licks
        if reopen:
            # Clear existing data on the plot
            axes.clear()
            axes.set_xlim(0, 21)
            axes.set_ylim(0, self.controller.data_mgr.num_trials.get() + 1)

            if side == 1:
                # Iterate through the side one and two licks if available and plot them
                if self.controller.data_mgr.side_one_trial_licks:
                    for i, licks in enumerate(
                        self.controller.data_mgr.side_one_trial_licks
                    ):
                        if licks:
                            self.plot_licks(
                                axes, licks, i + 1, self.color_cycle(self.color_index)
                            )
                            self.color_index = (self.color_index + 1) % 10
            elif side == 2:
                if self.controller.data_mgr.side_two_trial_licks:
                    for i, licks in enumerate(
                        self.controller.data_mgr.side_two_trial_licks
                    ):
                        if licks:
                            self.plot_licks(
                                axes, licks, i + 1, self.color_cycle(self.color_index)
                            )
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
