import serial
import time
import threading
from typing import TYPE_CHECKING, Any
import queue
import serial.tools.list_ports
import logging

if TYPE_CHECKING:
    from program_control import ProgramController

logger = logging.getLogger(__name__)

class ArduinoManager:
    def __init__(self, controller: 'ProgramController') -> None:
        self.controller = controller
        self.BAUD_RATE = 115200
        self.laser_arduino = None
        self.motor_arduino = None
        self.data_queue: queue.Queue[Any] = queue.Queue()
        self.stop_event = threading.Event()

    def connect_to_arduino(self) -> None:
        """Connect to the Arduino boards and return status."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        for port in ports:
            identifier = self.identify_arduino(port)
            if identifier == "LASER":
                self.laser_arduino = serial.Serial(port, self.BAUD_RATE)
                logger.info(f"Laser Arduino connected on port {port}")
            elif identifier == "MOTOR":
                self.motor_arduino = serial.Serial(port, self.BAUD_RATE)
                logger.info(f"Motor Arduino connected on port {port}")

        if self.motor_arduino is None:
            error_message = "Motor Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            self.controller.display_gui_error("Motor Arduino Error", error_message)
            logger.error(error_message)
        else:
            command = 'S'
            self.send_command_to_laser(command)
            logger.info("Connected to Arduino boards successfully.")

        self.listener_thread = threading.Thread(target=self.listen_for_serial, daemon=True)
        self.listener_thread.start()
        logger.info("Started listening thread for Arduino serial input.")
        self.controller.process_queue()

    def listen_for_serial(self):
        while not self.stop_event.is_set():
            try:
                if self.laser_arduino and self.laser_arduino.in_waiting > 0:
                    laser_data = self.laser_arduino.readline().decode('utf-8').strip()
                    self.data_queue.put(('laser', laser_data))
                    logger.info(f"Received from laser: {laser_data}")

                if self.motor_arduino and self.motor_arduino.in_waiting > 0:
                    motor_data = self.motor_arduino.readline().decode('utf-8').strip()
                    self.data_queue.put(('motor', motor_data))
                    logger.info(f"Received from motor: {motor_data}")
            except Exception as e:
                logger.error(f"Error reading from Arduino: {e}")
                break
            time.sleep(0.001)

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
            arduino.write(command.encode("utf-8"))
            arduino.flush()  # Ensure buffer is flushed after sending command
            identifier = arduino.readline().decode("utf-8").strip()
            arduino.close()
            logger.info(f"Arduino on port {port} identified as {identifier}")
            return identifier
        except Exception as e:
            error_message = f"An error occurred while identifying Arduino: {e}"
            self.controller.display_gui_error("Error Identifying Arduino", error_message)
            logger.error(error_message)
            return "ERROR"

    def reset_arduinos(self) -> None:
        """Send a reset command to both Arduino boards."""
        try:
            if self.laser_arduino and self.motor_arduino:
                self.laser_arduino.write(b'R')
                self.laser_arduino.flush()  # Flush after sending command
                self.motor_arduino.write(b'R')
                self.motor_arduino.flush()  # Flush after sending command
                logger.info("Arduino boards reset.")
            else:
                logger.error("Arduino boards not connected.")
        except Exception as e:
            error_message = f"Error resetting Arduino boards: {e}"
            self.controller.display_gui_error("Error resetting Arduino boards:", error_message)
            logger.error(error_message)

    def send_command_to_motor(self, command) -> None:
        """Send a specific command to the motor Arduino."""
        try:
            if self.motor_arduino:
                self.motor_arduino.flush()  # Flush before sending command
                self.motor_arduino.write(command.encode("utf-8"))
                self.motor_arduino.flush()  # Flush after sending command
                logger.info(f"Sent command to motor: {command}")
            else:
                logger.error("Motor Arduino not connected.")
        except Exception as e:
            error_message = f"Error sending command to motor Arduino: {e}"
            self.controller.display_gui_error("Error sending command to motor Arduino:", error_message)
            logger.error(error_message)
        
    def send_command_to_laser(self, command) -> None:            
        """Send a specific command to the laser Arduino."""
        try:
            if self.laser_arduino:
                self.laser_arduino.flush()  # Flush before sending command
                self.laser_arduino.write(command.encode("utf-8"))
                self.laser_arduino.flush()  # Flush after sending command
                logger.info(f"Sent command to laser: {command}")
            else:
                logger.error("Laser Arduino not connected.")
        except Exception as e:
            error_message = f"Error sending command to laser Arduino: {e}"
            self.controller.display_gui_error("Error sending command to laser Arduino:", error_message)
            logger.error(error_message)

    def close_connections(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.laser_arduino is not None:
            self.laser_arduino.close()
        if self.motor_arduino is not None:
            self.motor_arduino.close()
        logger.info("Closed connections to Arduino boards.")
