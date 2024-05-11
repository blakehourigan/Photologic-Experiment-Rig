import serial # type: ignore
import time
import threading
from typing import TYPE_CHECKING
import queue
import serial.tools.list_ports #type: ignore

if TYPE_CHECKING:
    from program_control import ProgramController

class AduinoManager:
    def __init__(self, controller: 'ProgramController') -> None:
        self.controller = controller

        self.BAUD_RATE = 115200
        self.laser_arduino = None
        self.motor_arduino = None
        self.data_queue = queue.Queue()  #type: ignore
        self.stop_event = threading.Event()

    def connect_to_arduino(self) -> None:
        """Connect to the Arduino boards and return status."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        for port in ports:
            identifier = self.identify_arduino(port)
            if identifier == "LASER":
                self.laser_arduino = serial.Serial(port, self.BAUD_RATE)
            elif identifier == "MOTOR":
                self.motor_arduino = serial.Serial(port, self.BAUD_RATE)

        # if self.laser_arduino is None:
        #     error_message = "Laser Arduino not connected. Connect Arduino boards and relaunch before running the program."
        #     self.close_connections() 
        #     self.controller.display_gui_error(
        #         "Laser Arduino Error", error_message
        #     )
        if self.motor_arduino is None:
            error_message = "Motor Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            self.controller.display_gui_error(
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
        while not self.stop_event.is_set():
            try:
                if self.laser_arduino and self.laser_arduino.in_waiting > 0:
                    laser_data = self.laser_arduino.readline().decode('utf-8').strip()
                    self.data_queue.put(('laser', laser_data))

                if self.motor_arduino and self.motor_arduino.in_waiting > 0:
                    motor_data = self.motor_arduino.readline().decode('utf-8').strip()
                    self.data_queue.put(('motor', motor_data))
                    print(motor_data)
            except Exception as e:
                print(f"Error reading from Arduino: {e}")
                break
            time.sleep(.001)

    def stop(self) -> None:
        self.stop_event.set()
        if self.listener_thread.is_alive():
            self.listener_thread.join()


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
            self.controller.display_gui_error(
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
            self.controller.display_gui_error(
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
            self.controller.display_gui_error(
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
            self.controller.display_gui_error(
                "Error sending command to laser Arduino:", e
            )
    
    def close_connections(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.laser_arduino is not None:
            self.laser_arduino.close()
        if self.motor_arduino is not None:
            self.motor_arduino.close()
        print("Closed connections to Arduino boards.")
