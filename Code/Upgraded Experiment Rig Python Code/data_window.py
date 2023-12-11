import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import matplotlib.pyplot as plt

class DataWindow:
    def __init__(self, controller) -> None:
        self.controller = controller 
        self.top = None
        
            
    def show_window(self) -> None:
        if self.top is not None and self.top.winfo_exists():
            self.top.lift()       
        else:
            self.top = self.create_window(self.top)

    def create_window(self, master) -> None:
        # if the program schedule has been generated, then create the window
        if self.controller.data_mgr.blocks_generated:
            self.top = tk.Toplevel(self.controller.root)
            self.top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event

            container = tk.Frame(self.top)
            container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            # Create a figure and axes for the plot
            self.fig, self.axes = plt.subplots()
            
            # create a canvas that will hold the figure. The canvas is set to be held in the window instance
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