import serial # type: ignore
import time
import re
import traceback
import threading
from typing import List
import queue
import serial.tools.list_ports #type: ignore


class AduinoManager:
    def __init__(self, controller) -> None:
        self.controller = controller

        self.BAUD_RATE = 115200
        self.laser_arduino = None
        self.motor_arduino = None
        self.data_queue = queue.Queue()  #type: ignore

    def connect_to_arduino(self) -> None:
        """Connect to the Arduino boards and return status."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        for port in ports:
            identifier = self.identify_arduino(port)
            if identifier == "LASER":
                self.laser_arduino = serial.Serial(port, self.BAUD_RATE)
            elif identifier == "MOTOR":
                self.motor_arduino = serial.Serial(port, self.BAUD_RATE)

        if self.laser_arduino is None:
            error_message = "Laser Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections() 
            self.controller.main_gui.display_error(
                "Laser Arduino Error", error_message
            )
        if self.motor_arduino is None:
            error_message = "Motor Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            self.controller.main_gui.display_error(
                "Motor Arduino Error", error_message
            )
        else:
            command = 'S'
            self.send_command_to_laser(command)
            print("Connected to Arduino boards successfully.")
        

        self.listener_thread = threading.Thread(target=self.listen_for_serial, daemon=True)
        self.listener_thread.start()
        print("Started listening thread for Arduino serial input.")
        self.controller.process_queue()

            

    def listen_for_serial(self):
        while True:
            try:
                if self.laser_arduino and self.laser_arduino.in_waiting > 0:
                    laser_data = self.laser_arduino.readline().decode('utf-8').strip()
                    print(laser_data)
                    self.data_queue.put(('laser', laser_data))

                if self.motor_arduino and self.motor_arduino.in_waiting > 0:
                    motor_data = self.motor_arduino.readline().decode('utf-8').strip()
                    print(motor_data)
                    self.data_queue.put(('motor', motor_data))

            except Exception as e:
                print(f"Error reading from Arduino: {e}")
                break

            time.sleep(0.1)


    def identify_arduino(self, port) -> str:
        """Identify the Arduino on the given port."""
        try:
            arduino = serial.Serial(port, self.BAUD_RATE, timeout=1)
            command = "<W>"
            time.sleep(2)
            arduino.write((command.encode("utf-8")))
            identifier = arduino.readline().decode("utf-8").strip()
            arduino.close()
            return identifier
        except Exception as e:
            error_message = f"An error occurred while identifying Arduino: {e}"
            self.controller.main_gui.display_error(
                "Error Identifying Arduino", error_message
            )
            return "ERROR"

    def reset_arduinos(self) -> None:
        """Send a reset command to both Arduino boards."""
        try:
            if self.laser_arduino and self.motor_arduino:
                self.laser_arduino.write(b'R')
                self.motor_arduino.write(b'R')
                print("Arduino boards reset.")
            else:
                print("Arduino boards not connected.")
        except Exception as e:
            self.controller.main_gui.display_error(
                "Error resetting Arduino boards:", e
            )

    def send_command_to_motor(self, command) -> None:
        """Send a specific command to the motor Arduino."""
        try:
            if self.motor_arduino:
                self.motor_arduino.write(command.encode("utf-8"))
                self.motor_arduino.flush()
            else:
                print("Motor Arduino not connected.")
        except Exception as e:
            self.controller.main_gui.display_error(
                "Error sending command to motor Arduino:", e
            )
        
    def send_command_to_laser(self, command) -> None:            
        """Send a specific command to the laser Arduino."""
        try:
            if self.laser_arduino:
                self.laser_arduino.write(command.encode("utf-8"))
                self.laser_arduino.flush()
            else:
                print("Laser Arduino not connected.")
        except Exception as e:
            self.controller.main_gui.display_error(
                "Error sending command to laser Arduino:", e
            )


    def send_schedule_to_motor(self) -> None:
        """Send a schedule to the motor Arduino and receive an echo for confirmation."""
        try:
            stim_var_list = list(self.controller.data_mgr.stimuli_vars.values())
            
            filtered_stim_var_list = [item for item in stim_var_list if not re.match(r'Valve \d+ substance', item.get())]
            
            side_one_vars = []
            side_two_vars = []
            
            self.side_one_indexes: List[int] = [] 
            self.side_two_indexes: List[int] = []
            
            for i in range(len(filtered_stim_var_list)):
                if i < len(filtered_stim_var_list) // 2:  
                    side_one_vars.append(filtered_stim_var_list[i].get())
                else:
                    side_two_vars.append(filtered_stim_var_list[i].get())

            if self.motor_arduino:            
                side_one_schedule = self.controller.data_mgr.stimuli_dataframe['Side 1'] # separating the schedules based on side

                side_two_schedule = self.controller.data_mgr.stimuli_dataframe['Side 2']
                
                for i in range(len(side_one_schedule)):     
                    index = side_one_vars.index(side_one_schedule[i])
                    self.side_one_indexes.append(index)
                    index = side_two_vars.index(side_two_schedule[i])
                    self.side_two_indexes.append(index)
                
                side_one_index_str = ",".join(map(str, self.side_one_indexes))
                side_two_index_str = ",".join(map(str, self.side_two_indexes))
                
                command = f"<S,Side One,{side_one_index_str},-1,Side Two,{side_two_index_str},-1,end>"
                self.send_command_to_motor(command)  # Signal to Arduino about the upcoming command

        except Exception as e:
            error_message = traceback.format_exc()  # Capture the full traceback
            print(f"Error sending schedule to motor Arduino: {error_message}")  # Print the error to the console or log
            self.controller.main_gui.display_error("Error sending schedule to motor Arduino:", str(e))

    def verify_schedule(self, side_one_indexes, side_two_indexes, verification):
        middle_index = len(verification) // 2

        # Split the list into two halves
        side_one_verification_str = verification[:middle_index]
        side_two_verification_str = verification[middle_index:]
        
        side_one_verification = [int(x) for x in side_one_verification_str.split(',') if x.strip().isdigit()]
        side_two_verification = [int(x) for x in side_two_verification_str.split(',') if x.strip().isdigit()]
        
        are_equal_side_one = all(side_one_indexes[i] == side_one_verification[i] for i in range(len(side_one_indexes)))
        are_equal_side_two = all(side_two_indexes[i] == side_two_verification[i] for i in range(len(side_two_indexes)))
        
        if are_equal_side_one and are_equal_side_two:
            print("Both lists are identical, Schedule Send Complete.")
        else:
            print("Lists are not identical.")
    
    """concatinate the positions with the commands that are used to tell the arduino which side we are opening the valve for. 
    SIDE_ONE tells the arduino we need to open a valve for side one, it will then read the next line to find which valve to open.
    valves are numbered 1-8 so "SIDE_ONE\n1\n" tells the arduino to open valve one for side one. """
    
    
    def close_connections(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.laser_arduino is not None:
            self.laser_arduino.close()
        if self.motor_arduino is not None:
            self.motor_arduino.close()
        print("Closed connections to Arduino boards.")
