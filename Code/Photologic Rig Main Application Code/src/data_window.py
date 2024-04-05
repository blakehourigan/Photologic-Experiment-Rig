from typing import Optional
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import matplotlib.pyplot as plt

class DataWindow:
    def __init__(self, controller) -> None:
        self.controller = controller 
        self.master = controller.main_gui.root
        
        self.top: Optional[tk.Toplevel] = None
    
    def show_window(self) -> None:
        if self.top is not None and self.top.winfo_exists():
            self.top.lift()       
        elif not self.controller.data_mgr.blocks_generated:
            messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")
        else:
          self.top = self.create_window()
          self.create_plot()

    def create_window(self) -> tk.Toplevel:
        # if the program schedule has been generated, then create the window    
            top = tk.Toplevel(self.master)
            top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event
            top.bind("<Control-w>", lambda e: top.destroy())  # Close the window when the user presses ctl + w
            # Set the favicon of the child window to match the main window
            top.iconbitmap(self.master.iconbitmap())
            
            return top
        
    def create_plot(self) -> None:
        container = tk.Frame(self.top)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create a figure and axes for the plot
        self.fig, self.axes = plt.subplots()

        # Initialize an empty list to store spike times
        self.spike_times = [] #type: ignore

        # Set the x and y limits
        self.axes.set_xlim(0, 15)  # 15-second window on the x-axis
        self.axes.set_ylim(0, self.controller.data_mgr.num_trials.get())  # Range from 0 to num_trials on the y-axis
        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Trial #')

        # Create a canvas that will hold the figure
        self.canvas = FigureCanvasTkAgg(self.fig, container)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Create a toolbar for the plot and pack it into the window
        toolbar = NavigationToolbar2Tk(self.canvas, container)
        toolbar.update()

    def update_plot(self, lick_times=None, trial_index=None):
        # Clear the previous plot
        self.axes.clear()

        # Set the x and y limits
        self.axes.set_xlim(0, 15) # 0 to 15 seconds
        self.axes.set_ylim(0, self.controller.data_mgr.num_trials.get()) # 0 to num_trials trials

        # If lick_times and trial_index are provided, plot the lick times on the specified trial
        if lick_times is not None and trial_index is not None:
            self.axes.scatter(lick_times, [trial_index] * len(lick_times), marker='|', c='r', s=100)

        # Redraw the canvas
        self.canvas.draw()

    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None