import serial
import serial.tools.list_ports
import toml
import json
import time
import threading
from typing import Any
import queue
import logging
import numpy as np

from views.gui_common import GUIUtils


logger = logging.getLogger(__name__)


class ArduinoManager:
    def __init__(self, exp_data, process_queue_callback) -> None:
        self.BAUD_RATE = 115200
        self.laser_arduino = None
        self.motor_arduino = None

        self.exp_data = exp_data
        self.arduino_data = exp_data.arduino_data

        self.process_queue_callback = process_queue_callback

        self.data_queue: queue.Queue[Any] = queue.Queue()
        self.stop_event = threading.Event()

        self.connect_to_arduino()

    def connect_to_arduino(self) -> None:
        """Connect to the Arduino boards and return status."""
        ports = serial.tools.list_ports.comports()
        arduino_ports = []

        # find the arduino boards so we don't waste time trying to connect to empty ports
        for p in ports:
            if p.manufacturer is not None and "Arduino" in p.manufacturer:
                arduino_ports.append(p)

        for port in arduino_ports:
            port = port.device
            # get either LASER or MOTOR device identifier from the boards
            identifier = self.identify_device_port(port)
            match identifier:
                case "LASER":
                    self.laser_arduino = serial.Serial(port, self.BAUD_RATE)
                    logger.info(f"Laser Arduino connected on port {port}")
                case "MOTOR":
                    self.motor_arduino = serial.Serial(port, self.BAUD_RATE)
                    logger.info(f"Motor Arduino connected on port {port}")
                case _:
                    logger.info(
                        "response recieved but not recognized as laser or motor"
                    )

        if self.laser_arduino is None:
            error_message = "Laser Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            GUIUtils.display_error("Laser Arduino Not Found", error_message)
            logger.error(error_message)

        if self.motor_arduino is None:
            error_message = "Motor Arduino not connected. Connect Arduino boards and relaunch before running the program."
            self.close_connections()
            GUIUtils.display_error("Motor Arduino Not Found", error_message)
            logger.error(error_message)
        else:
            # tell laser arduino that the program starts now
            laser = self.laser_arduino
            start_command = "S".encode("utf-8")
            self.send_command(board=laser, command=start_command)
            logger.info("Connected to Arduino boards successfully.")

    def listen_for_serial(self):
        while 1:
            if self.stop_event.is_set():
                break
            try:
                if self.laser_arduino.in_waiting > 0:
                    laser_data = self.laser_arduino.readline().decode("utf-8").strip()
                    self.data_queue.put(("laser", laser_data))

                if self.motor_arduino.in_waiting > 0:
                    motor_data = self.motor_arduino.readline().decode("utf-8").strip()
                    self.data_queue.put(("motor", motor_data))
            except Exception as e:
                logger.error(f"Error reading from Arduino: {e}")
                break
            time.sleep(0.001)

    def stop_listener_thread(self) -> None:
        """
        method to set the stop event for the listener thread and
        join it back to the main program thread
        """
        self.stop_event.set()
        if self.listener_thread.is_alive():
            self.listener_thread.join()

    def identify_device_port(self, port) -> str:
        """Identify the Arduino on the given port."""
        try:
            arduino = serial.Serial(port, self.BAUD_RATE, timeout=1)
            time.sleep(1)
            # send command Who are you'
            command = "WHO ARE YOU\n"

            self.send_command(arduino, command.encode("utf-8"))

            # identifier returned from arduino, either LASER or MOTOR"
            identifier = arduino.readline().decode("utf-8").strip()
            arduino.close()

            logger.info(f"Arduino on port {port} identified as {identifier}")
            return identifier
        except Exception as e:
            error_message = f"Device on {port} is not an arduino {e}"
            logger.info(error_message)
            return None

    def reset_arduinos(self) -> None:
        """
        Send a reset command to both Arduino boards.
        """
        arduinos = [self.laser_arduino, self.motor_arduino]
        try:
            for board in arduinos:
                if board:
                    command = "RESET\n".encode("utf-8")
                    board.write(command)

                    logger.info(f"{board} Arduino reset.")
                else:
                    logger.error(f"Arduino {board} connection error.")
        except Exception as e:
            error_message = f"Error resetting Arduino boards: {e}"
            GUIUtils.display_error("Error resetting Arduino boards:", error_message)
            logger.error(error_message)

    def close_connections(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.laser_arduino is not None:
            self.laser_arduino.close()
        if self.motor_arduino is not None:
            self.motor_arduino.close()
        logger.info("Closed connections to Arduino boards.")

    def send_experiment_variables(self):
        """
        This method is defined to send program variables num_stimuli and num_trials to
        the motor arduino. This is useful because it allows the arduino to understand how long schedules should be (num_trials),
        and what valve should be selected for side 2 (num_stimuli).
        """
        num_stimuli = self.exp_data.exp_var_entries["Num Stimuli"]
        num_trials = self.exp_data.exp_var_entries["Num Trials"]

        motor = self.motor_arduino

        # 2 np 8 bit numbers converted to raw bytes
        num_stimuli = np.int8(num_stimuli).tobytes()
        num_trials = np.int8(num_trials).tobytes()

        var_comm = "REC VAR\n".encode("utf-8")
        self.send_command(motor, var_comm)

        packet = num_stimuli + num_trials
        self.send_command(motor, packet)

    def send_experiment_schedule(self):
        """
        Method to send valve schedule to the motor arduino so it know which valve to
        open on a given trial.
        First load np schedule arrays for both sides, turn them into bytes, and
        set them back to back in a packet. i.e side two will follow side one
        """
        side_one, side_two = self.arduino_data.load_schedule_indices()
        schedule_packet = side_one.tobytes() + side_two.tobytes()

        sched_command = "REC SCHED\n".encode("utf-8")

        motor = self.motor_arduino
        self.send_command(motor, sched_command)

        self.send_command(motor, schedule_packet)

        self.verify_schedule(motor, side_one, side_two)

    def send_valve_durations(self):
        # get side_one and side_two durations from the arduino data model
        # will load from arduino_data.toml from the last_used class by default
        # durations can be reset by passing reset_durations=True
        side_one, side_two = self.arduino_data.load_durations()

    def verify_schedule(self, arduino, side_one, side_two):
        """
        Method to tell motor arduino to give us the schedules that it
        recieved. It will send data byte by byte in the order that it
        recieved it (side one schedule, then side two) it will send EXACTLY
        num_trials * 2 bytes (8 bit / 1 byte int for each trial on each side).
        if successful we continue execution and log success message.
        """
        try:
            motor = self.motor_arduino
            ver_sched_command = "VER SCHED\n".encode("utf-8")
            self.send_command(motor, ver_sched_command)

            num_trials = self.exp_data.exp_var_entries["Num Trials"]

            ver1 = np.zeros((num_trials,), dtype=np.int8)
            ver2 = np.zeros((num_trials,), dtype=np.int8)

            # wait for the data to arrive
            while arduino.in_waiting < 0:
                pass
            for i in range(num_trials):
                ver1[i] = arduino.read()
            for i in range(num_trials):
                ver2[i] = arduino.read()
            logger.info(f"Arduino recieved side one as => {ver1}")
            logger.info(f"Arduino recieved side two as => {ver2}")

            if np.array_equal(side_one, ver1) and np.array_equal(side_two, ver2):
                logger.info(
                    "Motor arduino has recieved and verified experiment valve schedule"
                )
            else:
                GUIUtils.display_error(
                    "======SCHEDULE ERROR======",
                    "MOTOR ARDUINO did not recieve the correct schedule. Please restart the program and attempt\
                        schedule generation again.",
                )
        except Exception as e:
            logger.error(f"error verifying arduino schedule {e}")

    @staticmethod
    def send_command(board, command) -> None:
        """Send a specific command to the motor Arduino."""
        try:
            if board:
                # Flush before sending command
                board.write(command)
                logger.info(f"Sent {command} to -> motor: ")
            else:
                logger.error("{board} Arduino not connected.")
        except Exception as e:
            error_message = f"Error sending command to motor Arduino: {e}"
            GUIUtils.display_error(
                "Error sending command to motor Arduino:", error_message
            )
            logger.error(error_message)
