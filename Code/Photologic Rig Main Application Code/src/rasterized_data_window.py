from typing import Optional
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib.cm as cm


class RasterizedDataWindow:
    def __init__(self, controller) -> None:
        self.controller = controller 
        self.master = controller.main_gui.root
        
        self.side1_window: Optional[tk.Toplevel] = None
        self.side2_window: Optional[tk.Toplevel] = None
        
        self.color_cycle = cm.get_cmap('tab10', 10)  # Initialize the color cycle
        self.color_index = 0  # Initialize the color index
    
    def show_window(self, side: int) -> None:
        if side == 1:
            target_window = self.side1_window
        else:
            target_window = self.side2_window
        
        if target_window is not None and target_window.winfo_exists():
            target_window.lift()
        elif not self.controller.data_mgr.blocks_generated:
            messagebox.showinfo("Blocks Not Generated", "Experiment blocks haven't been generated yet, please generate trial blocks and try again")
        else:
            if side == 1:
                self.side1_window = self.create_window(side)
                self.create_plot(self.side1_window, side)
            else:
                self.side2_window = self.create_window(side)
                self.create_plot(self.side2_window, side)


    def create_window(self, side: int) -> tk.Toplevel:
        top = tk.Toplevel(self.master)
        top.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(side))
        top.bind("<Control-w>", lambda e, x=side: self.on_window_close(x)) # type: ignore 
        top.iconbitmap(self.master.iconbitmap())  # Assuming master has a set icon
        top.title(f"Side {side} Raster Plot")
        return top

        
    def create_plot(self, window: tk.Toplevel, side: int) -> None:
        container = tk.Frame(window)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        fig, axes = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, container)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        toolbar = NavigationToolbar2Tk(canvas, container)
        toolbar.update()
        
        if side == 1:
            self.update_plot(axes)
        else:
            self.update_plot(axes)

        canvas.draw()

    def update_plot(self, axes, lick_times=None, trial_index=None):

        # Set the x and y limits
        axes.set_xlim(0, 21)  # 0 to 15 seconds
        axes.set_ylim(0, self.controller.data_mgr.num_trials.get() + 1)  # 0 to num_trials trials
        
        # Plot the spike times
        if (lick_times is not None) and len(lick_times) > 0:
            # If lick_times and trial_index are provided, plot the lick times on the specified trial
            if lick_times is not None and trial_index is not None:
                color = self.color_cycle(self.color_index)  # Get the current color from the color cycle
                lick_times = [stamp - lick_times[0] for stamp in lick_times]  # Perform the calculation
                axes.scatter(lick_times, [trial_index] * len(lick_times), marker='|', c=color, s=100)
                self.color_index = (self.color_index + 1) % 10  # Update the color index for the next call

            # If lick_times and trial_index are None, plot the data from self.trial_licks
            elif lick_times is None and trial_index is None:
                for trial_index, trial_lick_times in enumerate(self.controller.data_mgr.trial_licks):
                    color = self.color_cycle(self.color_index)  # Get the current color from the color cycle
                    trial_lick_times = [stamp - trial_lick_times[0] for stamp in trial_lick_times]  # Perform the calculation
                    axes.scatter(trial_lick_times, [trial_index + 1] * len(trial_lick_times), marker='|', c=color, s=100)
                    self.color_index = (self.color_index + 1) % 10  # Update the color index for the next call

            for window in [self.side1_window, self.side2_window]:
                # Redraw the canvas
                window.canvas.draw()
    
    def on_window_close(self, side: int) -> None:
        """Close both side windows when one is closed."""
        if self.side1_window is not None:
            self.side1_window.destroy()
            self.side1_window = None
        if self.side2_window is not None:
            self.side2_window.destroy()
            self.side2_window = None
