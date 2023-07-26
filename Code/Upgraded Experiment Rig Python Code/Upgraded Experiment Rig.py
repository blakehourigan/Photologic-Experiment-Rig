import serial
import time
import tkinter as tk
from tkinter import scrolledtext
import random
#import pandas as pd

PORT1 = 'COM3'
PORT2 = 'COM4'
BAUD_RATE = 9600


class App:
    # Initialize the App object
    def __init__(self):
        # Create a Tkinter window
        self.root = tk.Tk()
        # Set the initial size of the window
        self.root.geometry("1280x720")
        # Set the title of the window
        self.root.title("Upgraded Experiment Rig")

        # Configure the GUI grid layout
        for i in range(7):
            self.root.grid_rowconfigure(i, weight=1 if i == 3 else 0)
        for i in range(4):
            self.root.grid_columnconfigure(i, weight=1)

        self.state = "None"

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

        # Program information label
        self.program_label = tk.Label(text="Program Information", bg="light blue", font=("Helvetica", 24))
        self.program_label.grid(row=2, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)

        # Start/stop button
        self.startButton = tk.Button(text="Start", command=self.startToggle, bg="green", font=("Helvetica", 24))
        self.startButton.grid(row=1, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)
        # Clear screen button
        self.clearButton = tk.Button(text="Clear", command=self.toggle, bg="grey", font=("Helvetica", 24))
        self.clearButton.grid(row=1, column=2, pady=10, padx=10, sticky='nsew', columnspan=2)


        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)
        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # Create a scrolled text widget for displaying data, place it in the frame, and set it to expand with the frame
        self.data_text = scrolledtext.ScrolledText(self.frame, font=("Helvetica", 24), height=10, width=30)
        self.data_text.grid(row=0, column=0, sticky='nsew')

        # Initialize the running flag to False
        self.running = False
        # Initialize the start time to 0
        self.start_time = 0
        self.leftLicks = 0
        self.rightLicks = 0 

         # Generate random numbers
        self.random_numbers = [random.randint(-5000, 5000) for _ in range(3)]

        # Initialize the interval variables and their corresponding StringVars

        self.interval1_var = tk.StringVar()
        self.interval1_var.set(str(30000))

        self.interval2_var = tk.StringVar()
        self.interval2_var.set(str(15000))

        self.interval3_var = tk.StringVar()
        self.interval3_var.set(str(15000))

        # Add Data Entry widgets for intervals
        self.interval1_entry = tk.Entry(self.root, textvariable=self.interval1_var, font=("Helvetica", 24))
        self.interval1_entry.grid(row=6, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2_entry = tk.Entry(self.root, textvariable=self.interval2_var, font=("Helvetica", 24))
        self.interval2_entry.grid(row=6, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3_entry = tk.Entry(self.root, textvariable=self.interval3_var, font=("Helvetica", 24))
        self.interval3_entry.grid(row=6, column=2, pady=10, padx=10, sticky='nsew')

        # Add button to update intervals
        self.update_button = tk.Button(text="Update Intervals", command=self.update_intervals, bg="grey", font=("Helvetica", 24))
        self.update_button.grid(row=6, column=3, pady=10, padx=10, sticky='nsew')

        self.intervals      = [int(self.interval1_var.get()),int(self.interval2_var.get()),int(self.interval3_var.get())]


        # Open a serial connection to the first Arduino
        self.arduinoLaser = serial.Serial('COM3', 9600)
        # Open a serial connection to the second Arduino
        self.arduinoMotor = serial.Serial('COM4', 9600)

        # Wait for the serial connections to settle
        time.sleep(2)

        # Start the clock and the data reader
        self.update_clock()
        self.read_licks()



    # State methods

    def initial_time_interval(self):
        if self.running:
            self.state = "ITI"
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            self.state_start_time = time.time()  # Update the state start time
            self.append_data('Initial Interval: ' + str((int(self.interval1_var.get()) + self.random_numbers[0]) / 1000) + "s\n")
            self.root.after((self.intervals[0] + self.random_numbers[0]), self.time_to_contact)


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

    # Define the method for toggling the program state
    def startToggle(self):
        # If the program is running, stop it
        if self.running:
            self.running = False
            self.startButton.configure(text="Start", bg="green")
            # Send the reset command to both Arduinos
            self.arduinoLaser.write(b'reset\n')
            self.arduinoMotor.write(b'reset\n')
            self.random_numbers = [random.randint(-5000, 5000) for _ in range(3)]
        # If the program is not running, start it
        else:
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

    def update_intervals(self):
    # Update the interval variables based on the values in the Entry widgets
        try:
            self.interval1 = int(self.interval1_var.get())
            self.interval2 = int(self.interval2_var.get())
            self.interval3 = int(self.interval3_var.get())
        except ValueError:
            # If the user didn't enter a valid integer, show an error message
            tk.messagebox.showerror("Error", "Please enter a valid integer for the intervals.")


# Create an App object
app = App()
# Start the Tkinter event loop
app.root.mainloop()

# Close the serial connections to the Arduinos
app.arduinoLaser.close()
app.arduinoMotor.close()
