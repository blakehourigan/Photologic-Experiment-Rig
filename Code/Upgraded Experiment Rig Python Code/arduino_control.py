import serial
import time

import serial.tools.list_ports


class AduinoManager:
    def __init__(self, controller) -> None:
        self.pg_controller = controller
        
        self.BAUD_RATE = 9600 
        self.arduinoLaser = None
        self.arduinoMotor = None

    def connect_to_arduino(self) -> None:
        """Connect to the Arduino boards and return status."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        for port in ports:
            identifier = self.identify_arduino(port)
            if identifier == "LASER":
                self.arduinoLaser = serial.Serial(port, self.BAUD_RATE)
            elif identifier == "MOTOR":
                self.arduinoMotor = serial.Serial(port, self.BAUD_RATE)

        if self.arduinoLaser is None or self.arduinoMotor is None:
            error_message = "1 or more Arduino boards are not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            self.pg_controller.display_error("Serial Connection Error", error_message)
        else:
            print("Connected to Arduino boards successfully.")

    def identify_arduino(self, port) -> str:
        """Identify the Arduino on the given port."""
        try:
            arduino = serial.Serial(port, self.BAUD_RATE, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            arduino.write(b'WHO_ARE_YOU\n')
            identifier = arduino.readline().decode('utf-8').strip()
            arduino.close()
            return identifier
        except Exception as e:
            print(f"An error occurred while identifying Arduino: {e}")
            return "ERROR"
        
    def reset_arduinos(self) -> None:
        """Send a reset command to both Arduino boards."""
        try:
            if self.arduinoLaser and self.arduinoMotor:
                self.arduinoLaser.write(b'reset\n')
                self.arduinoMotor.write(b'reset\n')
                print("Arduino boards reset.")
            else:
                print("Arduino boards not connected.")
        except Exception as e:
            self.pg_controller.display_error("Error resetting Arduino boards:", e)

    def send_command_to_motor(self, command) -> None:
        """Send a specific command to the motor Arduino."""
        try:
            if self.arduinoMotor:
                self.arduinoMotor.write(command.encode('utf-8'))
                self.arduinoMotor.flush()
            else:
                print("Motor Arduino not connected.")
        except Exception as e:
            self.pg_controller.display_error("Error sending command to motor Arduino:", e)

    def close_connections(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.arduinoLaser is not None:
            self.arduinoLaser.close()
        if self.arduinoMotor is not None:
            self.arduinoMotor.close()
        print("Closed connections to Arduino boards.")