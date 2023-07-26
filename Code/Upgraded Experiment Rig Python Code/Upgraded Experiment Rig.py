import serial
import time
import tkinter as tk
from tkinter import scrolledtext
import random
#import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

BAUD_RATE = 9600

class App:
    # Initialize the App object
    def __init__(self):
        # Create a Tkinter window
        self.root = tk.Tk()
        # Set the initial size of the window
        self.root.geometry("1400x800")
        # Set the title of the window
        self.root.title("Upgraded Experiment Rig")

        # Initialize the interval variables and their corresponding IntVars
        self.interval_vars = {
            'ITI_var': tk.IntVar(value=30000),
            'TTC_var': tk.IntVar(value=15000),
            'sample_time_var': tk.IntVar(value=15000),
            'interval1Rand_var': tk.IntVar(value=5000),
            'interval2Rand_var': tk.IntVar(value=5000),
            'interval3Rand_var': tk.IntVar(value=5000),
        }

        # Initialize dictionary fill of stimulus variables and fill each entry to hold value equal to the key value
        self.stimuli_vars = {f'stimuli_var_{i+1}': tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)

        self.num_trials = tk.IntVar()
        self.num_trials.set(0)
        self.num_stimuli = tk.IntVar()
        self.num_stimuli.set(0)

        # Initialize the running flag to False
        self.running = False
        # Initialize the start time to 0
        self.start_time = 0
        self.leftLicks = 0
        self.rightLicks = 0 
        self.data_window_open = False

         # Generate random numbers
        self.randomITI = random.randint(-(self.interval_vars['interval1Rand_var'].get()), (self.interval_vars['interval1Rand_var'].get()))
        self.randomTTC = random.randint(-(self.interval_vars['interval2Rand_var'].get()), (self.interval_vars['interval2Rand_var'].get()))
        self.randomSample = random.randint(-(self.interval_vars['interval3Rand_var'].get()), (self.interval_vars['interval3Rand_var'].get()))

        self.intervals      = [(self.interval_vars['ITI_var'].get()),(self.interval_vars['TTC_var'].get()),(self.interval_vars['sample_time_var'].get())]

        self.state = "OFF"

        # Configure the GUI grid layout
        for i in range(8):
            self.root.grid_rowconfigure(i, weight=1 if i == 3 else 0)
        # The column is also configured to expand
        self.root.grid_columnconfigure(0, weight=1)


        # Label headers
        self.time_label_header = tk.Label(text="Elapsed Time:", bg="light blue", font=("Helvetica", 24))
        self.time_label_header.grid(row=0, column=0, pady=10, padx=10, sticky='e')

        self.state_time_label_header = tk.Label(text=(self.state), bg="light blue", font=("Helvetica", 24))
        self.state_time_label_header.grid(row=0, column=2, pady=10, padx=10, sticky='e')

        # Timer labels
        self.time_label = tk.Label(text="", bg="light blue", font=("Helvetica", 24))
        self.time_label.grid(row=0, column=1, pady=10, padx=10, sticky='w')

        self.state_time_label = tk.Label(text="", bg="light blue", font=("Helvetica", 24))
        self.state_time_label.grid(row=0, column=3, pady=10, padx=10, sticky='w')

        # Labels for Interval Entry widgets
        self.interval1_label = tk.Label(self.root, text="Initial Interval:", bg="light blue", font=("Helvetica", 24))
        self.interval1_label.grid(row=5, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2_label = tk.Label(self.root, text="Time to Contact:", bg="light blue", font=("Helvetica", 24))
        self.interval2_label.grid(row=5, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3_label = tk.Label(self.root, text="Time to Sample:", bg="light blue", font=("Helvetica", 24))
        self.interval3_label.grid(row=5, column=2, pady=10, padx=10, sticky='nsew')

        # Add Data Entry widgets for intervals
        self.interval1_entry = tk.Entry(self.root, textvariable=self.interval_vars['ITI_var'], font=("Helvetica", 24))
        self.interval1_entry.grid(row=6, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2_entry = tk.Entry(self.root, textvariable=self.interval_vars['TTC_var'], font=("Helvetica", 24))
        self.interval2_entry.grid(row=6, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3_entry = tk.Entry(self.root, textvariable=self.interval_vars['sample_time_var'], font=("Helvetica", 24))
        self.interval3_entry.grid(row=6, column=2, pady=10, padx=10, sticky='nsew')

        # Labels for Interval Entry widgets
        self.interval1_label = tk.Label(self.root, text="+/- (All times in ms)", bg="light blue", font=("Helvetica", 24))
        self.interval1_label.grid(row=7, column=0, pady=10, padx=10, sticky='nsew', columnspan=3)

        # Label for # of trials
        self.num_trials_label = tk.Label(self.root, text="# of Trials", bg="light blue", font=("Helvetica", 24))
        self.num_trials_label.grid(row=5, column=3, pady=10, padx=10, sticky='nsew')

        # Entry for # of trials
        self.num_trials_entry = tk.Entry(self.root, textvariable=self.num_trials, font=("Helvetica", 24))
        self.num_trials_entry.grid(row=6, column=3, pady=10, padx=10, sticky='nsew')

        # Label for # stimuli
        self.num_stimuli_label = tk.Label(self.root, text="# of Stimuli", bg="light blue", font=("Helvetica", 24))
        self.num_stimuli_label.grid(row=7, column=3, pady=10, padx=10, sticky='nsew')

        # Entry for # of trials
        self.num_stimuli_entry = tk.Entry(self.root, textvariable=self.num_stimuli, font=("Helvetica", 24))
        self.num_stimuli_entry.grid(row=8, column=3, pady=10, padx=10, sticky='nsew')

        # Add Data Entry widgets for random plus/minus intervals
        self.interval1Rand_entry = tk.Entry(self.root, textvariable=self.interval_vars['interval1Rand_var'], font=("Helvetica", 24))
        self.interval1Rand_entry.grid(row=8, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2Rand_entry = tk.Entry(self.root, textvariable=self.interval_vars['interval2Rand_var'], font=("Helvetica", 24))
        self.interval2Rand_entry.grid(row=8, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3Rand_entry = tk.Entry(self.root, textvariable=self.interval_vars['interval3Rand_var'], font=("Helvetica", 24))
        self.interval3Rand_entry.grid(row=8, column=2, pady=10, padx=10, sticky='nsew')

        # Program information label
        self.program_label = tk.Label(text="Program Information", bg="light blue", font=("Helvetica", 24))
        self.program_label.grid(row=2, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)

        # Start/stop button
        self.startButton = tk.Button(text="Start", command=self.start_toggle, bg="green", font=("Helvetica", 24))
        self.startButton.grid(row=1, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)

        # Clear screen button
        self.clearButton = tk.Button(text="Clear", command=self.toggle, bg="grey", font=("Helvetica", 24))
        self.clearButton.grid(row=1, column=2, pady=10, padx=10, sticky='nsew', columnspan=2)

        # Add button to update intervals
        self.update_button = tk.Button(text="Update Settings", command=self.update_intervals, bg="grey", font=("Helvetica", 24))
        self.update_button.grid(row=9, column=0, pady=10, padx=10, sticky='nsew',columnspan=4)

        # button to open the stimuli window
        self.stimuli_window_button = tk.Button(text="Edit Stimuli", command=self.stimuli_window, bg="grey", font=("Helvetica", 24))
        self.stimuli_window_button.grid(row=10, column=0, pady=10, padx=10, sticky='nsew')

        # button to open the data window
        self.data_window_button = tk.Button(text="View Data", command=self.data_window, bg="grey", font=("Helvetica", 24))
        self.data_window_button.grid(row=10, column=1, pady=10, padx=10, sticky='nsew')


        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)
        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # Create a scrolled text widget for displaying data, place it in the frame, and set it to expand with the frame
        self.data_text = scrolledtext.ScrolledText(self.frame, font=("Helvetica", 24), height=10, width=30)
        self.data_text.grid(row=0, column=0, sticky='nsew')


        # Open a serial connection to the first Arduino
        self.arduinoLaser = serial.Serial('COM3', BAUD_RATE)
        # Open a serial connection to the second Arduino
        self.arduinoMotor = serial.Serial('COM4', BAUD_RATE)

        # Wait for the serial connections to settle
        time.sleep(2)

        # Start the clock and the data reader
        self.update_clock()
        self.read_licks()

    def stimuli_window(self):
        try:
            # Try to lift the window to the top (it will fail if the window is closed)
            self.stimuli_window_instance.lift()
        except (AttributeError, tk.TclError):
            self.stimuli_window_instance = tk.Toplevel(self.root)
            self.stimuli_window_instance.geometry("800x550")
            self.stimuli_window_instance.title("Stimuli")

            for i in range(self.num_stimuli.get()):
                # Decide column based on iteration number
                column = 0 if i < 4 else 1
                # Adjust row for the second column
                row = 2 * (i % 4)

                # Labels/Entry boxes for Stimuli
                label = tk.Label(self.stimuli_window_instance, text=f"Stimuli {i+1}", bg="light blue", font=("Helvetica", 24))
                label.grid(row=row, column=column, pady=10, padx=10, sticky='nsew')

                entry = tk.Entry(self.stimuli_window_instance, textvariable=self.stimuli_vars[f'stimuli_var_{i+1}'], font=("Helvetica", 24))
                entry.grid(row=row+1, column=column, pady=10, padx=10, sticky='nsew')



    def data_window(self):
        try:
            # Try to lift the window to the top (it will fail if the window is closed)
            self.data_window_instance.lift()
        except (AttributeError, tk.TclError):
            # If the window is closed, create a new one
            self.data_window_instance = tk.Toplevel(self.root)
            self.data_window_instance.geometry("800x600")
            self.data_window_instance.title("Data")

            # Override the default close behavior
            self.data_window_instance.protocol("WM_DELETE_WINDOW", self.close_data_window)

            # Create a figure and axes for the plot
            self.fig, self.axes = plt.subplots()
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.data_window_instance)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            # Create a toolbar for the plot and pack it into the window
            toolbar = NavigationToolbar2Tk(self.canvas, self.data_window_instance)
            toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.update_plot()
        # Update the plot only if the window is open
        if self.data_window_open:
            self.update_plot()
            self.root.after(100, self.data_window)
        else:
            self.data_window_open = False

    def update_plot(self):
        self.axes.clear()  # clear the old plot
        self.axes.plot(self.rightLicks, color='black')  # draw the new plot
        self.canvas.draw()  # update the canvas
    def update_data_label(self):
        # Update the label text only if the window is open
        if self.data_window_open:
            self.data_label_var.set("Updated text")
            self.root.after(100, self.update_data_label)

    def close_data_window(self):
        self.data_window_open = False
        self.data_window_instance.destroy()



    # State methods

    def initial_time_interval(self):
        if self.running:
            self.state = "ITI"
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            self.state_start_time = time.time()  # Update the state start time
            self.append_data('Initial Interval: ' + str(((self.interval_vars['ITI_var'].get()) + random.randint(-self.interval_vars['interval1Rand_var'].get(), self.interval_vars['interval1Rand_var'].get())) / 1000) + "s\n")
            self.root.after((self.interval_vars['ITI_var'].get() + self.random_numbers[0]), self.time_to_contact)


    def time_to_contact(self):
        if self.running:
            self.state = "TTC"
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            self.state_start_time = 0
            self.state_start_time = time.time()  # Update the state start time
            target_position = "-6400"
            self.arduinoMotor.write(target_position.encode())
            self.append_data('Time to Contact: ' + str((self.intervals[1] + self.random_numbers[1]) / 1000) + "s\n")
            self.root.after((self.intervals[1] + self.random_numbers[1]), self.sample_time)

    def sample_time(self):
        if self.running:
            self.state = "Sample"
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            self.state_start_time = 0
            self.state_start_time = time.time()  # Update the state start time
            self.append_data('Sample Time Interval: ' + str((self.intervals[2] + self.random_numbers[2]) / 1000) + "s\n")

    # Define the method for sending the target position
    def send_target_position(self):
        # Get the target position from the entry widget
        target_position = self.position_entry.get()
        # Send the target position to the second Arduino
        self.arduinoMotor.write(target_position.encode())

    def toggle(self):
        # Clear the scrolled text widget
        self.data_text.delete('1.0', tk.END)
        elapsed_time = 0 
        self.time_label.configure(text="{:.3f}s".format(elapsed_time))
        state_elapsed_time = 0
        self.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))

    def update_intervals(self):
    # Update the interval variables based on the values in the Entry widgets
        try:
            print('hey')
        except ValueError:
            # If the user didn't enter a valid integer, show an error message
            tk.messagebox.showerror("Error", "Please enter a valid integer for the intervals.")

    # Define the method for toggling the program state
    def start_toggle(self):
        # If the program is running, stop it
        if self.running:
            self.state = "OFF"
            self.state_time_label_header.configure(text=(self.state))
            self.running = False
            self.startButton.configure(text="Start", bg="green")
            # Send the reset command to both Arduinos
            self.arduinoLaser.write(b'reset\n')
            self.arduinoMotor.write(b'reset\n')
        # If the program is not running, start it
        else:
            # Start the program if it is not already runnning, generate random intervals for each trial.
            self.running = True
            self.start_time = time.time()
            self.startButton.configure(text="Stop", bg="red")
            self.initial_time_interval()

    # Define the method for updating the clock
    def update_clock(self):
        # If the program is running, update the elapsed time
        if self.running:
            elapsed_time = time.time() - self.start_time
            self.time_label.configure(text="{:.3f}s".format(elapsed_time))
            state_elapsed_time = time.time() - self.state_start_time
            self.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
        # Call this method again after 100 ms
        self.root.after(100, self.update_clock)

    # Define the method for reading data from the first Arduino
    def read_licks(self):
        # If there is data available from the first Arduino, read it
        if self.arduinoLaser.in_waiting > 0:
            data = self.arduinoLaser.read(self.arduinoLaser.in_waiting).decode('utf-8')
            # Append the data to the scrolled text widget
            if "Left Lick" in data:
                self.leftLicks += 1
                self.append_data(data)
                self.append_data(str(self.leftLicks))
            if "Right Lick" in data:
                self.rightLicks += 1 
                self.append_data(str(self.rightLicks))
        # Call this method again after 100 ms
        self.root.after(100, self.read_licks)

    # Define the method for appending data to the scrolled text widget
    def append_data(self, data):
        self.data_text.insert(tk.END, data)
        # Scroll the scrolled text widget to the end of the data
        self.data_text.see(tk.END)


# Create an App object
app = App()
# Start the Tkinter event loop
app.root.mainloop()

# Close the serial connections to the Arduinos
app.arduinoLaser.close()
app.arduinoMotor.close()
