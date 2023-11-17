import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

class DataWindow:
    def __init__(self) -> None:
        try:
            # Try to lift the window on top of all windows (it will fail if the window is closed)
            self.data_window_instance.lift()
        except (AttributeError, tk.TclError):
            # cancel any previous calls to update the plot
            if self.update_plot_id is not None:
                self.root.after_cancel(self.update_plot_id)
            # if the program schedule has been generated, then create the window
            if self.blocks_generated:
                self.data_window_instance = self.window_instance_generator("Data", "800x600")

                # Create a figure and axes for the plot
                self.fig, self.axes = plt.subplots()
                # create a canvas that will hold the figure. The canvas is set to be held in the window instance
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.data_window_instance)
                # Set the canvas to start at the top of the window instance and fill the window, expanding the content as the user expands the window 
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                # Create a toolbar for the plot and pack it into the window
                toolbar = NavigationToolbar2Tk(self.canvas, self.data_window_instance)
                toolbar.update()

                # update the plot with data in this function call 
                self.update_plot()
            else:
                # if blocks haven't been generated, let the user know that they need to do that before they can use this page.
                #messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")
                pass