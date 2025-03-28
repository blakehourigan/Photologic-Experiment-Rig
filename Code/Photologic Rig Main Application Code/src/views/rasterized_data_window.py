"""
Defines the RasterizedDataWindow class, a Tkinter Toplevel window designed
to display lick event data as a raster plot using Matplotlib figures.

This view provides a visualization of lick timestamps for a specific recording side (e.g., Port 1 or Port 2),
plotting each lick as a marker against trial number and time within the trial (relative to the first lick).
It updates as new trial data becomes available.
"""

import tkinter as tk
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk

### Type Hinting###
from models.experiment_process_data import ExperimentProcessData
### Type Hinting###


class RasterizedDataWindow(tk.Toplevel):
    """
    A Toplevel window creating a Matplotlib raster plot to visualize lick events.

    This window displays lick timestamps for a specific experimental side (passed during
    initialization) against the trial number. Each lick within a trial is plotted
    as a vertical marker (|). The time axis typically represents the time elapsed since
    the first lick in that trial. The plot updates as new lick data arrives
    via the `update_plot` method.

    Attributes
    ----------
    - **exp_data** (*ExperimentProcessData*): An instance holding experiment-related data,
      including trial parameters (`exp_var_entries`) used for setting Y-axis plot limits.
    - **color_cycle** (*Colormap*): A Matplotlib colormap instance (`tab10`) used
      to cycle through colors for plotting data from different trials/updates.
      In other words, makes it easier to distinguish trials.
    - **color_index** (*int*): The current index into the `color_cycle`.
    - **canvas** (*FigureCanvasTkAgg | None*): The Matplotlib canvas widget embedded in the
      Tkinter window. Initialized in `create_plot`.
    - **axes** (*Axes | None*): The Matplotlib axes object where the raster
      plot is drawn. Initialized in `create_plot`.

    Methods
    -------
    - `show()`
        Makes the window visible.
    - `create_plot()`
        Creates the initial Matplotlib figure, axes, canvas, and toolbar. Sets axis limits.
    - `update_plot(lick_times, logical_trial)`
        Adds lick data for a specific trial to the plot and redraws the canvas.
    """

    def __init__(self, side: int, exp_data: ExperimentProcessData) -> None:
        """
        Initializes the RasterizedDataWindow. Sets basic window attributes and initializes class attributes.

        Parameters
        ----------
        - **side** (*int*): The experimental side (e.g., 1 or 2) this plot represents.
        - **exp_data** (*ExperimentProcessData*): The data object containing experiment parameters
          and facilitates event data access.
        """
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
        """
        Unhides the window.
        """
        self.deiconify()

    def create_plot(self) -> None:
        """
        Creates the Matplotlib figure, axes, canvas, and toolbar, and sets initial properties.

        Sets up a container frame. Initializes the Matplotlib figure and axes.
        Sets the X and Y axis limits based on expected time range and total trial number.
        Adds labels to the axes and a title to the plot. Plades the figure
        in a Tkinter canvas and adds the navigation toolbar. Assigns the created
        components to instance attributes `self.fig`, `self.axes`, and `self.canvas`.

        Raises
        ------
        - *KeyError*: If "Num Trials" is not found in `self.exp_data.exp_var_entries`.
        - *tk.TclError*: If Tkinter widget creation or packing fails.
        """
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
        lick_times: Optional[list[float]] = None,
        logical_trial: Optional[int] = None,
    ) -> None:
        """
        Adds lick data for a specific trial to the raster plot and redraws the canvas.

        Checks if the plot components (`axes`, `canvas`) have been initialized.
        If `lick_times` data is provided and valid, it calculates the time relative
        to the first lick in the trial, assigns a color based on the trial index,
        and plots the lick times as vertical markers ('|') at the corresponding
        `logical_trial` row using `scatter`. Finally, it redraws the canvas to display
        the updated plot.

        Parameters
        ----------
        - **lick_times** (*Optional[List[float]]*): A list of timestamps (in seconds) for licks
          recorded during the trial. If None or empty, the plot is not updated for this trial.
        - **logical_trial** (*Optional[int]*): The zero-based index of the trial corresponding
          to the `lick_times`. Used as the Y-coordinate for plotting. If None, the plot is not updated.

        Raises
        ------
        - *TypeError*: If `logical_trial` is not an integer when provided.
        - *IndexError*: Potentially if `lick_times` is accessed incorrectly (though unlikely with current logic).
        """
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
