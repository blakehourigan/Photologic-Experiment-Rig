from typing import Optional
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import matplotlib.pyplot as plt
import numpy as np

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
            
            return top
        
    def create_plot(self) -> None:
        container = tk.Frame(self.top)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create a figure and axes for the plot
        self.fig, self.axes = plt.subplots()

        # Generate random spike times for multiple neurons (replace with your actual data)
        num_neurons = 10
        spike_times = [np.random.rand(100) * 10 for _ in range(num_neurons)]

        # Create the raster plot
        for i, spikes in enumerate(spike_times):
            self.axes.scatter(spikes, [i] * len(spikes), marker='|', s=100)

        self.axes.set_xlabel('Time')
        self.axes.set_ylabel('Neuron')

        # Create a canvas that will hold the figure. The canvas is set to be held in the window instance
        self.canvas = FigureCanvasTkAgg(self.fig, container)

        # Set the canvas to start at the top of the window instance and fill the window, expanding the content as the user expands the window
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Create a toolbar for the plot and pack it into the window
        toolbar = NavigationToolbar2Tk(self.canvas, container)
        toolbar.update()

    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None