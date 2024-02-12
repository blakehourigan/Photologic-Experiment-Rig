import serial # type: ignore
import time
from typing import Optional, Tuple

import serial.tools.list_ports #type: ignore


class AduinoManager:
    def __init__(self, controller) -> None:
        self.controller = controller

        self.BAUD_RATE = 115200
        self.laser_arduino = None
        self.motor_arduino = None

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

    def identify_arduino(self, port) -> str:
        """Identify the Arduino on the given port."""
        try:
            arduino = serial.Serial(port, self.BAUD_RATE, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            arduino.write(b'W')
            identifier = arduino.readline().decode("utf-8").strip()
            print(identifier)
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

    def send_schedule_to_motor(self, schedule) -> None:
        """Send a schedule to the motor Arduino and receive an echo for confirmation."""
        try:
            if self.motor_arduino:     
                stim_var_list = list(self.controller.data_mgr.stimuli_vars.values())
                side_one_vars = []
                side_two_vars = []
                
                for sv in stim_var_list:
                    print(sv.get(), end="\n")    
                                
                for i in range(len(stim_var_list)):
                    if i in range(0,len(stim_var_list)/2):
                        side_one_vars.append(stim_var_list[i])
                    else:
                        side_two_vars.append(stim_var_list[i])
           
                for item in schedule:
                    for index, string_var in enumerate(side_one_vars):
                        if string_var.get() == item :
                            self.stim1_position = str(index + 1)
                    for index, string_var in enumerate(side_two_vars):
                        # repeat process for the second stimulus
                        if string_var.get() == item :
                            self.stim2_position = str(index + 1)
                            
                    for sv in side_one_vars:
                        print(sv.get(), end="hi")    
                    
                    for sv in side_two_vars:
                        print(sv.get())                        
                    
                    
                    print(item[0], self.stim1_position, item[1], self.stim2_position)
                    
                    self.send_command_to_motor('S') # tell the arduino that we're about to start sending the sched
                    
                    clean_item_0 = item[0].replace(" ", "")
                    clean_item_1 = item[1].replace(" ", "")
                    
                    string = f'{clean_item_0},{clean_item_1}'
                    print(f"Sending: {string}")
                    
                    self.send_command_to_motor(string)
                    self.motor_arduino.reset_input_buffer()  # Clear buffer before reading
                    
                    time.sleep(2)

                    data = self.motor_arduino.read(self.motor_arduino.in_waiting).decode(
                        "utf-8"
                    )                    
                    print(f"Received Echo: {data}")
                print('Schedule Send Complete.')
        except Exception as e:
            self.controller.main_gui.display_error(
                "Error sending schedule to motor Arduino:", e
            )



    def read_from_laser(self) -> Tuple[bool, Optional[str]]:
        """Read data from the laser Arduino."""
        data = ""
        available = False
        stimulus: Optional[str] = None
        if (
            self.laser_arduino is not None
        ):  # if arduino laser is connected, read serial data
            if self.laser_arduino.in_waiting > 0:
                data = self.laser_arduino.read(self.laser_arduino.in_waiting).decode(
                    "utf-8"
                )
                available = True
            if available:
                if "Stimulus One Lick" in data:
                    stimulus = "Stimulus 1"
                if "Stimulus Two Lick" in data:
                    stimulus = "Stimulus 2"
        return (available, stimulus)
    
    
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
