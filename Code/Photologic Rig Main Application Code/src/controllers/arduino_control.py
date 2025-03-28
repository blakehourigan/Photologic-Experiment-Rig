"""
This module is used to establish communication with the Arduino board. It sends information like schedule, experiment variable, and
valve duration information to the boar, along with other commands important for the operation of the Experiment Rig.
"""

import serial
import serial.tools.list_ports
import time
import threading
import queue
import logging
import numpy as np

### USED FOR TYPE HINTING ###
from models.experiment_process_data import ExperimentProcessData
import numpy.typing as npt
### USED FOR TYPE HINTING ###

from views.gui_common import GUIUtils


logger = logging.getLogger(__name__)

# each side has 8 valves, therefore 8 durations in each array
VALVES_PER_SIDE = 8


class ArduinoManager:
    """
    This class establishes a Serial connection to the Arduino board and facilitates communication of information between the board and the controlling
    PC. All actions involving the Arduino are managed here.

    Attributes
    ----------
    - **BAUD_RATE** (*int*): This holds the class constant baud rate which is essentially the max rate of communication between the Arduino and the PC.
    - **arduino** (*serial.Serial*): This variable hold the serial.Serial information for the Arduino. This includes what physical port the board is
    connected to, baud rate and more.
    - **exp_data** (*ExperimentProcessData*): An instance of `models.experiment_process_data` ExperimentProcessData, this variable allows access to
    important program attributes like num_trials and program schedules that need to be send to the arduino board.
    - **arduino_data** (*ArduinoData*): This is a reference to the program instance of `models.arduino_data` ArduinoData. It allows access to this
    class and its methods which allows ArduinoManager to load data stored there such as valve duration times and schedule indicies.
    - **data_queue** (*queue.Queue[tuple[str, str]]*): This is the queue that facilitates data transmission between the arduino's `listener_thread`,
    which constantly listens for any data coming from the arduino board. This queue is processed in the `app_logic` method `process_queue`. This allows
    the main thread to do other important work, only processing arduino information every so often, if there is any to process.
    - **stop_event** (*threading.Event*): This event is set in the class method `stop_listener_thread`. This is a thread safe data type that allows
    us to exit the listener thread to avoid leaving threads busy when exiting the main application.
    - **listener_thread** (*threading.Thread | None*): Previously discussed peripherally, this is the thread that listens constantly for new information
    from the arduino board. The threads target method is the `listen_for_serial` method.

    Methods
    -------
    - `connect_to_arduino`()
        Scans available ports for devices named 'Arduino' to establish a connection with the Arduino board.
    - `listen_for_serial`()
        Continuously listens for incoming serial data from the Arduino, adding received messages to `data_queue`.
    - `stop_listener_thread`()
        Signals the listener thread to stop and safely joins it back to the main thread.
    - `reset_arduino`()
        Sends a reset command to the Arduino board. Used after connection is established to clear any residual data on the board.
    - `close_connection`()
        Closes the serial connection to the Arduino board.
    - `send_experiment_variables`()
        Transmits experimental variables (number of stimuli and trials) to the Arduino for schedule configuration.
    - `send_schedule_data`()
        Sends valve schedule data to the Arduino to define which valve should open on either side for a given trial.
    - `send_valve_durations`()
        Sends the calculated duration settings for each valve to the Arduino.
    - `verify_schedule`(side_one: npt.NDArray[np.int8], side_two: npt.NDArray[np.int8])
        Requests and verifies the valve schedule received by the Arduino by comparing against the sent values.
    - `verify_durations`(side_one: npt.NDArray[np.int32], side_two: npt.NDArray[np.int32])
        Requests and verifies the valve durations received by the Arduino by comparing against the sent values.
    - `send_command`(command: bytes)
        Sends a given command to the Arduino, ensuring communication reliability.
    """

    def __init__(self, exp_data: ExperimentProcessData) -> None:
        """
        Initialize and handle the ArduinoManager class. Here we establish the Arduino connection and reset the board to clear any
        residual data left on the Arduino board from previous experimental runs.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): An instance of `models.experiment_process_data` ExperimentProcessData. Used to access
        experiment variables and send them to the Arduino board.
        """
        self.BAUD_RATE: int = 115200
        self.arduino: None | serial.Serial = None

        self.exp_data = exp_data
        self.arduino_data = exp_data.arduino_data

        self.data_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.stop_event: threading.Event = threading.Event()
        self.listener_thread: threading.Thread | None = None

        # connect to the Arduino board if it is connected to the PC.
        self.connect_to_arduino()

        # reset the board fully to avoid improper communication on program 'reset'
        reset_arduino = "RESET\n".encode("utf-8")
        self.send_command(command=reset_arduino)

    def connect_to_arduino(self) -> None:
        """Connect to the Arduino board by searching all serial ports for a device with a manufacturer name 'Arduino'. If
        found, establish serial.Serial connection. If not notify user."""
        ports = serial.tools.list_ports.comports()
        arduino_port = None

        # find the arduino boards so we don't waste time trying to connect to empty ports
        for p in ports:
            if p.manufacturer is not None and "Arduino" in p.manufacturer:
                arduino_port = p

        # if we cannot find the arduino, no connection can be established, inform user and return.
        if arduino_port is None:
            error_message = (
                "Arduino not connected. Reconnect Arduino and relaunch the program."
            )
            GUIUtils.display_error("Arduino Not Found", error_message)
            logger.error(error_message)
            return
        else:
            port = arduino_port.device

            self.arduino = serial.Serial(port, self.BAUD_RATE)
            logger.info(f"Arduino connected on port {port}")

    def listen_for_serial(self) -> None:
        """
        Method to constantly scan for Arduino input. If received place in thread-save `data_queue` to process it later.
        """
        # if we do not have an arduino to listen to return and don't try to listen to it!
        if self.arduino is None:
            logger.error(
                "ARDUINO COMMUNICATION ERROR!!! Class attribute 'arduino' is None."
            )
            return

        while 1:
            if self.stop_event.is_set():
                break
            try:
                if self.arduino.in_waiting > 0:
                    data = self.arduino.readline().decode("utf-8").strip()
                    self.data_queue.put(("Arduino", data))

                    # log the received data
                    logger.info(f"Received -> {data} from arduino")
            except Exception as e:
                logger.error(f"Error reading from Arduino: {e}")
                break
            # sleep for a short time to avoid busy waiting
            time.sleep(0.001)

    def stop_listener_thread(self) -> None:
        """
        Method to set the stop event for the listener thread and
        join it back to the main program thread.
        """
        self.stop_event.set()

        if self.listener_thread is None:
            return

        if self.listener_thread.is_alive():
            self.listener_thread.join()

    def reset_arduino(self) -> None:
        """
        Send a reset command to the Arduino board.
        """
        try:
            command = "RESET\n".encode("utf-8")
            self.send_command(command)

            logger.info("Arduino reset.")
        except Exception as e:
            error_msg = f"Error resetting Arduino: {e}"

            GUIUtils.display_error("RESET ERROR", error_msg)
            logger.error(error_msg)

    def close_connection(self) -> None:
        """Close the serial connection to the Arduino board."""
        if self.arduino is not None:
            self.arduino.close()
        logger.info("Closed connections to Arduino.")

    def send_experiment_variables(self):
        """
        This method is defined to send program variables num_stimuli and num_trials to
        the Arduino. This is useful because it allows the Arduino to understand how long schedules should be (num_trials),
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

    def send_schedule_data(self) -> None:
        """
        Method to send valve schedule to the arduino so it know which valve to
        open on a given trial.
        First load np schedule arrays for both sides, turn them into bytes, and
        set them back to back in a packet. i.e side two will follow side one
        """
        side_one, side_two = self.arduino_data.load_schedule_indices()

        schedule_packet: bytes = side_one.tobytes() + side_two.tobytes()

        sched_command = "REC SCHED\n".encode("utf-8")

        self.send_command(sched_command)

        self.send_command(schedule_packet)

        self.verify_schedule(side_one, side_two)

    def send_valve_durations(self) -> None:
        """
        Get side_one and side_two durations from `models.arduino_data` Arduino data model
        will load from arduino_data.toml from the last_used 'profile'.
        """
        side_one, side_two, _ = self.arduino_data.load_durations()

        side_one_durs = side_one.tobytes()
        side_two_durs = side_two.tobytes()

        dur_packet = side_one_durs + side_two_durs

        dur_command = "REC DURATIONS\n".encode("utf-8")

        self.send_command(dur_command)

        self.send_command(dur_packet)

        self.verify_durations(side_one, side_two)

    def verify_schedule(
        self, side_one: npt.NDArray[np.int8], side_two: npt.NDArray[np.int8]
    ) -> None:
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

            if self.arduino is None:
                msg = "ARDUINO IS NOT CONNECTED! Try reconnecting and restart the program."
                logger.error(msg)
                GUIUtils.display_error("ARDUINO ERROR", msg)

                return

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

    def verify_durations(
        self, side_one: npt.NDArray[np.int32], side_two: npt.NDArray[np.int32]
    ) -> None:
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

            ver1 = np.zeros((VALVES_PER_SIDE,), dtype=np.int32)
            ver2 = np.zeros((VALVES_PER_SIDE,), dtype=np.int32)

            if self.arduino is None:
                msg = "ARDUINO IS NOT CONNECTED! Try reconnecting and restart the program."
                logger.error(msg)
                GUIUtils.display_error("ARDUINO ERROR", msg)

                return

            # wait for the data to arrive
            while self.arduino.in_waiting < 4 * 8:
                pass
            for i in range(VALVES_PER_SIDE):
                duration = int.from_bytes(
                    self.arduino.read(4), byteorder="little", signed=False
                )
                ver1[i] = duration
            for i in range(VALVES_PER_SIDE):
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

    def send_command(self, command: bytes):
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
