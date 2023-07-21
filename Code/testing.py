import serial
import time
import tkinter as tk
import tkinter.simpledialog as simpledialog

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.time_label = tk.Label(text="", bg="light blue", width=20, height=3)
        self.time_label.pack()
        self.button = tk.Button(text="Start", command=self.toggle, bg="green", width=20, height=3)
        self.button.pack()

        self.data_label = tk.Label(text="Data", bg="light blue", width=20, height=3)
        self.data_label.pack()
        
        self.frame = tk.Frame(self.root, width=400, height=200)
        self.frame.pack()

        self.data_text = tk.Text(self.frame, width=40, height=10)
        self.data_text.pack(side="left", fill="y")

        self.scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.data_text.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.data_text.configure(yscrollcommand=self.scrollbar.set)

        self.running = False
        self.start_time = 0

        # Create a serial object
        # Replace 'COM3' with the port where your Arduino is connected
        # Replace 9600 with the baud rate set in your Arduino program
        self.arduino = serial.Serial('COM3', 9600)

        # Allow some time for the connection to be established
        time.sleep(2)
        
        self.update_clock()
        self.read_data()

    def toggle(self):
        if self.running:
            self.running = False
            self.button.configure(text="Start", bg="green")
        else:
            self.running = True
            self.start_time = time.time()
            self.button.configure(text="Stop", bg="red")
            
            # Prompt the user to enter a target position
            target_position = simpledialog.askinteger("Target Position", "Enter a target position:")
            
            # Send the target position to the Arduino
            self.arduino.write(str(target_position).encode())

    def update_clock(self):
        if self.running:
            elapsed_time = time.time() - self.start_time
            self.time_label.configure(text="{:.3f}".format(elapsed_time))

        self.root.after(100, self.update_clock)  # update every 100 ms

    def read_data(self):
        # Check if there's data available at the serial port
        if self.arduino.in_waiting > 0:
            # Read all available data from the serial port
            data = self.arduino.read(self.arduino.in_waiting).decode('utf-8')
            
            # Schedule the append_data function to run on the main thread
            self.root.after(0, self.append_data, data)

        # Schedule the read_data function to run again after 100 ms
        self.root.after(100, self.read_data)

    def append_data(self, data):
        # Append the data from the Arduino to the text widget
        self.data_text.insert(tk.END, data)
        # Auto-scroll to the end
        self.data_text.see(tk.END)

app = App()
app.root.mainloop()

# Close the serial connection
app.arduino.close()
