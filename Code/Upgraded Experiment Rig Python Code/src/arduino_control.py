import serial
import time
from typing import Optional, Tuple

import serial.tools.list_ports


class AduinoManager:
    def __init__(self, controller) -> None:
        self.controller = controller

        self.BAUD_RATE = 9600
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
        elif self.motor_arduino is None:
            error_message = "Motor Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            self.controller.main_gui.display_error(
                "Motor Arduino Error", error_message
            )
        else:
            print("Connected to Arduino boards successfully.")

    def identify_arduino(self, port) -> str:
        """Identify the Arduino on the given port."""
        try:
            arduino = serial.Serial(port, self.BAUD_RATE, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            arduino.write(b"WHO_ARE_YOU\n")
            identifier = arduino.readline().decode("utf-8").strip()
            arduino.close()
            return identifier
        except Exception as e:
            print(f"An error occurred while identifying Arduino: {e}")
            return "ERROR"

    def reset_arduinos(self) -> None:
        """Send a reset command to both Arduino boards."""
        try:
            if self.laser_arduino and self.motor_arduino:
                self.laser_arduino.write(b"reset\n")
                self.motor_arduino.write(b"reset\n")
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

    def close_connections(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.laser_arduino is not None:
            self.laser_arduino.close()
        if self.motor_arduino is not None:
            self.motor_arduino.close()
        print("Closed connections to Arduino boards.")
