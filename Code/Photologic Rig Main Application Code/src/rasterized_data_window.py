import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from typing import TYPE_CHECKING, Optional
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from matplotlib.backends._backend_tk import NavigationToolbar2Tk

from gui_utils import GUIUtils

if TYPE_CHECKING:
    from program_control import ProgramController

class RasterizedDataWindow:
    def __init__(self, controller: 'ProgramController') -> None:
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
        top.protocol("WM_DELETE_WINDOW", self.on_any_window_close)
        top.bind("<Control-w>", lambda e: self.on_any_window_close())
        top.iconbitmap(self.master.iconbitmap())  # Assuming master has a set icon
        top.title(f"Side {side} Raster Plot")
        window_icon_path = self.controller.experiment_config.get_window_icon_path()
        GUIUtils.set_program_icon(top, icon_path=window_icon_path)
        
        return top

    def create_plot(self, window: tk.Toplevel, side: int) -> None:
        container = tk.Frame(window)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        fig, axes = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, container)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        toolbar = NavigationToolbar2Tk(canvas, container)
        toolbar.update()

        window.canvas = canvas  # type: ignore
        window.axes = axes      # type: ignore

        if len(self.controller.data_mgr.side_one_trial_licks) > 0 or len(self.controller.data_mgr.side_one_trial_licks) > 0:
            self.update_plot(window, reopen=True, side=side)  # Pass the whole window to update_plot
        else:
            self.update_plot(window)
        
    def update_plot(self, window: tk.Toplevel, lick_times=None, trial_index=None, reopen=False, side=0):
        axes = window.axes # type: ignore
        canvas = window.canvas # type: ignore
        
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
                    for i, licks in enumerate(self.controller.data_mgr.side_one_trial_licks):
                        if licks:
                            self.plot_licks(axes, licks, i + 1, self.color_cycle(self.color_index))
                            self.color_index = (self.color_index + 1) % 10
            elif side == 2:            
                if self.controller.data_mgr.side_two_trial_licks:
                    for i, licks in enumerate(self.controller.data_mgr.side_two_trial_licks):
                        if licks:
                            self.plot_licks(axes, licks, i + 1, self.color_cycle(self.color_index))
                            self.color_index = (self.color_index + 1) % 10
            
        if lick_times and len(lick_times) > 0:
            color = self.color_cycle(self.color_index)
            lick_times = [stamp - lick_times[0] for stamp in lick_times]
            axes.scatter(lick_times, [trial_index] * len(lick_times), marker='|', c=color, s=100)
            self.color_index = (self.color_index + 1) % 10

        canvas.draw()

    def plot_licks(self, axes, lick_times, trial_index, color):
        # Normalize lick times by the first lick time
        normalized_licks = [stamp - lick_times[0] for stamp in lick_times]
        axes.scatter(normalized_licks, [trial_index] * len(normalized_licks), marker='|', c=color, s=100)
        
    def on_any_window_close(self) -> None:
        if self.side1_window is not None:
            self.side1_window.destroy()
            self.side1_window = None
        if self.side2_window is not None:
            self.side2_window.destroy()
            self.side2_window = None
