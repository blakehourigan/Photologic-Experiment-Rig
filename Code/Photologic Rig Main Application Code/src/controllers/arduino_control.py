import serial
import serial.tools.list_ports
import time
import threading
from typing import Any
import queue
import logging
import numpy as np

from views.gui_common import GUIUtils


logger = logging.getLogger(__name__)


class ArduinoManager:
    def __init__(self, exp_data) -> None:
        self.BAUD_RATE = 115200
        self.arduino = None

        self.exp_data = exp_data
        self.arduino_data = exp_data.arduino_data

        self.data_queue: queue.Queue[Any] = queue.Queue()
        self.stop_event = threading.Event()
        self.listener_thread = None

        self.connect_to_arduino()

    def connect_to_arduino(self) -> None:
        """Connect to the Arduino boards and return status."""
        ports = serial.tools.list_ports.comports()
        arduino_port = None

        # find the arduino boards so we don't waste time trying to connect to empty ports
        for p in ports:
            if p.manufacturer is not None and "Arduino" in p.manufacturer:
                arduino_port = p

        if arduino_port is None:
            error_message = (
                "Arduino not connected. Reconnect Arduino and relaunch the program."
            )
            GUIUtils.display_error("Arduino Not Found", error_message)
            logger.error(error_message)
            return
        else:
            logger.info("Connected to Arduino boards successfully.")

        port = arduino_port.device

        self.arduino = serial.Serial(port, self.BAUD_RATE)
        logger.info(f"Arduino connected on port {port}")

    def listen_for_serial(self):
        while 1:
            if self.stop_event.is_set():
                break
            try:
                if self.arduino.in_waiting > 0:
                    data = self.arduino.readline().decode("utf-8").strip()
                    self.data_queue.put(("Arduino", data))
                    logger.info(f"Received -> {data} from arduino")
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

    def reset_arduino(self) -> None:
        """
        Send a reset command to both Arduino boards.
        """
        try:
            command = "RESET\n".encode("utf-8")
            self.arduino.write(command)
            logger.info("Arduino reset.")
        except Exception as e:
            error_msg = f"Error resetting Arduino: {e}"
            GUIUtils.display_error(error_msg)
            logger.error(error_msg)

    def close_connection(self) -> None:
        """Close the serial connections to the Arduino boards."""
        if self.arduino is not None:
            self.arduino.close()
        logger.info("Closed connections to Arduino.")

    def send_experiment_variables(self):
        """
        This method is defined to send program variables num_stimuli and num_trials to
        the arduino. This is useful because it allows the arduino to understand how long schedules should be (num_trials),
        and what valve should be selected for side 2 (num_stimuli).
        """
        num_stimuli = self.exp_data.exp_var_entries["Num Stimuli"]
        num_trials = self.exp_data.exp_var_entries["Num Trials"]

        # 2 np 8 bit numbers converted to raw bytes
        num_stimuli = np.int8(num_stimuli).tobytes()
        num_trials = np.int8(num_trials).tobytes()

        var_comm = "REC VAR\n".encode("utf-8")
        self.send_command(var_comm)

        packet = num_stimuli + num_trials
        self.send_command(packet)

    def send_experiment_schedule(self):
        """
        Method to send valve schedule to the arduino so it know which valve to
        open on a given trial.
        First load np schedule arrays for both sides, turn them into bytes, and
        set them back to back in a packet. i.e side two will follow side one
        """
        side_one, side_two = self.arduino_data.load_schedule_indices()
        schedule_packet = side_one.tobytes() + side_two.tobytes()

        sched_command = "REC SCHED\n".encode("utf-8")

        self.send_command(sched_command)

        self.send_command(schedule_packet)

        self.verify_schedule(side_one, side_two)

    def send_valve_durations(self):
        # get side_one and side_two durations from the arduino data model
        # will load from arduino_data.toml from the last_used class by default
        # durations can be reset by passing reset_durations=True
        side_one, side_two, date_used = self.arduino_data.load_durations()
        side_one_durs = side_one.tobytes()
        side_two_durs = side_two.tobytes()
        dur_packet = side_one_durs + side_two_durs

        dur_command = "REC DURATIONS\n".encode("utf-8")

        self.send_command(dur_command)

        self.send_command(dur_packet)

        self.verify_durations(side_one, side_two)

    def verify_schedule(self, side_one, side_two):
        """
        Method to tell arduino to give us the schedules that it
        recieved. It will send data byte by byte in the order that it
        recieved it (side one schedule, then side two) it will send EXACTLY
        num_trials * 2 bytes (8 bit / 1 byte int for each trial on each side).
        if successful we continue execution and log success message.
        """
        try:
            ver_sched_command = "VER SCHED\n".encode("utf-8")
            self.send_command(ver_sched_command)

            num_trials = self.exp_data.exp_var_entries["Num Trials"]

            ver1 = np.zeros((num_trials,), dtype=np.int8)
            ver2 = np.zeros((num_trials,), dtype=np.int8)

            # wait for the data to arrive
            while self.arduino.in_waiting < 0:
                pass
            for i in range(num_trials):
                ver1[i] = int.from_bytes(
                    self.arduino.read(), byteorder="little", signed=False
                )
            for i in range(num_trials):
                ver2[i] = int.from_bytes(
                    self.arduino.read(), byteorder="little", signed=False
                )
            logger.info(f"Arduino recieved side one as => {ver1}")
            logger.info(f"Arduino recieved side two as => {ver2}")

            if np.array_equal(side_one, ver1) and np.array_equal(side_two, ver2):
                logger.info(
                    "arduino has recieved and verified experiment valve schedule"
                )
            else:
                GUIUtils.display_error(
                    "======SCHEDULE ERROR======",
                    "ARDUINO did not recieve the correct schedule. Please restart the program and attempt\
                        schedule generation again.",
                )
        except Exception as e:
            logger.error(f"error verifying arduino schedule {e}")

    def verify_durations(self, side_one, side_two):
        """
        Method to tell arduino to give us the schedules that it
        recieved. It will send data byte by byte in the order that it
        recieved it (side one schedule, then side two) it will send EXACTLY
        num_trials * 2 bytes (8 bit / 1 byte int for each trial on each side).
        if successful we continue execution and log success message.
        """
        try:
            ver_dur_command = "VER DURATIONS\n".encode("utf-8")
            self.send_command(ver_dur_command)

            # each side has 8 valves, therefore 8 durations in each array
            valves_per_side = 8

            ver1 = np.zeros((valves_per_side,), dtype=np.int32)
            ver2 = np.zeros((valves_per_side,), dtype=np.int32)

            # wait for the data to arrive
            while self.arduino.in_waiting < 4 * 8:
                pass
            for i in range(valves_per_side):
                duration = int.from_bytes(
                    self.arduino.read(4), byteorder="little", signed=False
                )
                ver1[i] = duration
            for i in range(valves_per_side):
                duration = int.from_bytes(
                    self.arduino.read(4), byteorder="little", signed=False
                )
                ver2[i] = duration

            logger.info(f"Arduino recieved side one as => {ver1}")
            logger.info(f"Arduino recieved side two as => {ver2}")

            if np.array_equal(side_one, ver1) and np.array_equal(side_two, ver2):
                logger.info("arduino has recieved and verified valve durations")
            else:
                GUIUtils.display_error(
                    "======DURATIONS ERROR======",
                    "ARDUINO did not recieve the correct valve durations. Please restart the program and attempt\
                        schedule generation again.",
                )
        except Exception as e:
            logger.error(f"error verifying arduino durations -> {e}")

    def send_command(self, command):
        """
        Send a specific command to the Arduino. Command must be converted to raw bytes object
        before being passed into this method
        """
        if self.arduino is None:
            error_message = "Arduino connection was not established. Please reconnect the Arduino board and restart the program."
            GUIUtils.display_error(
                "====ARDUINO COMMUNICATION ERROR====:", error_message
            )
            logger.error(error_message)
            return

        try:
            self.arduino.write(command)
            logger.info(f"Sent {command} to arduino on -> {self.arduino.port}: ")
        except Exception as e:
            error_message = f"Error sending command to {self.arduino.port} Arduino: {e}"
            GUIUtils.display_error("Error sending command to Arduino:", error_message)
            logger.error(error_message)
