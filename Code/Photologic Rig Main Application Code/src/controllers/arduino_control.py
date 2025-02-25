import serial
import serial.tools.list_ports
import re
import json
import time
import threading
from typing import Any
import queue
import logging

from views.gui_common import GUIUtils


logger = logging.getLogger(__name__)


class ArduinoManager:
    def __init__(self, arduino_data) -> None:
        self.BAUD_RATE = 115200
        self.laser_arduino = None
        self.motor_arduino = None

        self.data_queue: queue.Queue[Any] = queue.Queue()
        self.stop_event = threading.Event()

        self.connect_to_arduino()
        time.sleep(2)

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

        if self.laser_arduino is None:
            error_message = "Laser Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            self.controller.display_gui_error("Laser Arduino Error", error_message)
            logger.error(error_message)

        if self.motor_arduino is None:
            error_message = "Motor Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            self.controller.display_gui_error("Motor Arduino Error", error_message)
            logger.error(error_message)
        else:
            command = "S"
            self.send_command_to_laser(command)
            logger.info("Connected to Arduino boards successfully.")

        self.listener_thread = threading.Thread(
            target=self.listen_for_serial, daemon=True
        )
        self.listener_thread.start()
        logger.info("Started listening thread for Arduino serial input.")
        self.controller.process_queue()

    def listen_for_serial(self):
        while 1:
            if self.stop_event.is_set():
                break
            try:
                if self.laser_arduino.in_waiting > 0:
                    laser_data = self.laser_arduino.readline().decode("utf-8").strip()
                    self.data_queue.put(("laser", laser_data))
                    logger.info(f"Received from laser: {laser_data}")

                if self.motor_arduino.in_waiting > 0:
                    motor_data = self.motor_arduino.readline().decode("utf-8").strip()
                    self.data_queue.put(("motor", motor_data))
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
            # send command <W> for '<W>ho are you?'
            command = "<W>"
            time.sleep(2)

            arduino.write(command.encode("utf-8"))
            # ensure all data is sent by flushing it out
            arduino.flush()
            # identifier returned from arduino, either LASER or MOTOR"

            identifier = arduino.readline().decode("utf-8").strip()
            arduino.close()

            logger.info(f"Arduino on port {port} identified as {identifier}")
            return identifier
        except Exception as e:
            error_message = f"An error occurred while identifying Arduino: {e}"
            GUIUtils.display_error("Error Identifying Arduino", error_message)
            logger.error(error_message)
            return "ERROR"

    def reset_arduinos(self) -> None:
        """Send a reset command to both Arduino boards."""
        arduinos = [self.laser_arduino, self.motor_arduino]
        try:
            for board in arduinos:
                if board:
                    board.write(b"R")
                    # Flush after sending command to ensure
                    board.flush()
                    logger.info(f"{board} Arduino reset.")
                else:
                    logger.error(f"Error resetting {board} arduino.")
        except Exception as e:
            error_message = f"Error resetting Arduino boards: {e}"
            self.controller.display_gui_error(
                "Error resetting Arduino boards:", error_message
            )
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
            self.controller.display_gui_error(
                "Error sending command to motor Arduino:", error_message
            )
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
            self.controller.display_gui_error(
                "Error sending command to laser Arduino:", error_message
            )
            logger.error(error_message)

    def close_connections(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.laser_arduino is not None:
            self.laser_arduino.close()
        if self.motor_arduino is not None:
            self.motor_arduino.close()
        logger.info("Closed connections to Arduino boards.")

    def send_data_to_motor(self, arduino_data) -> None:
        """Send a schedule to the motor Arduino and receive an echo for confirmation."""
        try:
            stim_var_list = list(self.stimuli_vars.values())
            filtered_stim_var_list = [
                item
                for item in stim_var_list
                if not re.match(r"Valve \d+ substance", item.get())
            ]
            side_one_vars = []
            side_two_vars = []

            side_one_indexes: List[int] = []
            side_two_indexes: List[int] = []

            for i in range(len(filtered_stim_var_list)):
                if i < len(filtered_stim_var_list) // 2:
                    side_one_vars.append(filtered_stim_var_list[i].get())
                else:
                    side_two_vars.append(filtered_stim_var_list[i].get())

            if self.controller.arduino_mgr.motor_arduino:
                side_one_schedule = self.stimuli_dataframe["Port 1"]
                side_two_schedule = self.stimuli_dataframe["Port 2"]

                for i in range(len(side_one_schedule)):
                    index = side_one_vars.index(side_one_schedule[i])
                    side_one_indexes.append(2**index)
                    index = side_two_vars.index(side_two_schedule[i])
                    side_two_indexes.append(2**index)

            arduino_data["side_one_schedule"] = side_one_indexes
            arduino_data["side_two_schedule"] = side_two_indexes

            self.save_configuration(config_data=arduino_data)

            logger.info("Updated json Schedule")
        except Exception as e:
            logger.error(f"Error sending schedule to motor Arduino: {e}")
            GUIUtils.display_error("Error sending schedule to motor Arduino:", str(e))
            raise

    def send_arduino_json_data(self, send_schedule=False):
        arduino_data = self.get_current_json_config()

        if send_schedule:
            self.data_mgr.send_data_to_motor(arduino_data=arduino_data)
            arduino_data = self.get_current_json_config()

        # Convert the dictionary to a JSON string
        json_data = json.dumps(arduino_data)

        time.sleep(2)

        arduino_command = "<A," + json_data + ">"

        self.send_command_to_arduino(arduino="motor", command=arduino_command)
