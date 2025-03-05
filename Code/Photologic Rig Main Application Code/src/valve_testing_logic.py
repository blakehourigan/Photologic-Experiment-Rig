import logging
from typing import List, Tuple, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from program_control import ProgramController


class valveTestLogic:
    def __init__(self, controller: "ProgramController") -> None:
        self.controller = controller
        self.side_one_volumes: List[int] = []
        self.side_two_volumes: List[int] = []
        self.side_one_durations: List[int] = []
        self.side_two_durations: List[int] = []
        self.completed_test_pairs = 0

    def start_valve_test_sequence(self, num_valves):
        """the test sequence that each valve will undergo"""
        logging.debug("Starting valve test sequence.")

        # Create a list of all the lists we use for the testing script, and clear each one of them to avoid problems with bad data
        for lst in [
            self.side_one_volumes,
            self.side_two_volumes,
            self.side_one_durations,
            self.side_two_durations,
        ]:
            lst.clear()

        self.completed_test_pairs = 0
        self.num_valves = num_valves

        logging.debug("Getting container measurements for both sides.")
        # Get the beaker measurements for the respective sides, set init to true to tell the popup to display the beaker measurement text.
        self.side_one_container_measurement = (
            self.controller.valve_testing_window.input_popup(0, init=True, side=1)
        )
        self.side_two_container_measurement = (
            self.controller.valve_testing_window.input_popup(0, init=True, side=2)
        )

        execute = self.check_container_measurements(
            self.side_one_container_measurement, self.side_two_container_measurement
        )
        logging.debug(
            f"Container measurements obtained: Side 1: {self.side_one_container_measurement}, Side 2: {self.side_two_container_measurement}, Execute: {execute}"
        )

        if execute:
            motor_command = f"<T,{num_valves.get()}>"
            logging.info(f"Sending command to Arduino: {motor_command}")
            self.controller.send_command_to_arduino(
                arduino="motor", command=motor_command
            )
        else:
            logging.warning(
                "Container measurements invalid, aborting valve test sequence."
            )

    def append_to_volumes(self) -> None:
        logging.debug("Appending to volumes.")
        self.side_one_volumes.append(
            self.controller.valve_testing_window.input_popup(
                self.completed_test_pairs + 1
            )
            - self.side_one_container_measurement
        )
        self.side_two_volumes.append(
            self.controller.valve_testing_window.input_popup(
                self.completed_test_pairs + 5
            )
            - self.side_two_container_measurement
        )
        logging.debug(
            f"Appended volumes: Side 1: {self.side_one_volumes[-1]}, Side 2: {self.side_two_volumes[-1]}"
        )

        execute = self.check_container_measurements(
            self.side_one_container_measurement, self.side_two_container_measurement
        )
        logging.debug(
            f"Container measurements check after appending volumes: Execute: {execute}"
        )

        if execute:
            if (
                self.completed_test_pairs
                != self.controller.valve_testing_window.num_valves_to_test.get()
            ):
                if self.controller.valve_testing_window.ask_continue():
                    logging.info("Sending continue command to Arduino.")
                    continue_command = "CONTINUE\n".encode("utf-8")
                    # need to change controller here / pass in ard_controller
                    self.controller.send_command_to_arduino(
                        arduino="motor", command=continue_command
                    )
                else:
                    logging.warning("Testing aborted by user.")
                    self.controller.valve_testing_window.testing_aborted()
                self.completed_test_pairs += 1
                logging.debug(f"Completed test pairs: {self.completed_test_pairs}")

    def begin_updating_opening_times(self, duration_string) -> None:
        logging.debug("Begin updating opening times.")
        json_config = self.controller.get_current_json_config()

        side_one_durations = json_config["valve_durations_side_one"]
        side_two_durations = json_config["valve_durations_side_two"]

        side_one_opening_times, side_one_ul_per_lick = self.update_opening_times(
            self.num_valves.get(), side_one_durations, self.side_one_volumes
        )
        side_two_opening_times, side_two_ul_per_lick = self.update_opening_times(
            self.num_valves.get(), side_two_durations, self.side_two_volumes
        )

        json_config["valve_durations_side_one"] = side_one_opening_times
        json_config["valve_durations_side_two"] = side_two_opening_times

        self.controller.update_valve_test_table(
            side_one_durations=side_one_opening_times,
            side_two_durations=side_two_opening_times,
            side_one_ul=side_one_ul_per_lick,
            Side_two_ul=side_two_ul_per_lick,
        )

        self.controller.save_current_json_config(json_config)

        # Convert the dictionary to a JSON string
        json_data = json.dumps(json_config)

        arduino_command = "<A," + json_data + ">"
        logging.info(f"Sending JSON data to Arduino: {arduino_command}")
        self.controller.send_command_to_arduino(
            arduino="motor", command=arduino_command
        )

    def update_opening_times(
        self, num_valves, durations, volumes
    ) -> Tuple[List[int], List[float]]:
        logging.debug("Updating opening times.")
        opening_times = []
        ul_dispensed = []

        # Get the desired volume entered in the testing window. This value is given in micro liter, divide by 1000 to get milliliters
        desired_volume = (
            self.controller.valve_testing_window.desired_volume.get()
        ) / 1000

        for i in range(num_valves // 2):
            v_per_open_previous = volumes[i] / 1000
            ul_dispensed.append(v_per_open_previous)
            opening_times.append(
                round(int(durations[i]) * (desired_volume / v_per_open_previous))
            )

        if (num_valves // 2) < 8:
            for i in range(8 - (num_valves // 2)):
                opening_times.append(durations[i + (num_valves // 2)])

        logging.debug(
            f"Updated opening times: {opening_times}, Ul per lick: {ul_dispensed}"
        )
        return opening_times, ul_dispensed

    def check_container_measurements(self, side_one, side_two) -> bool:
        logging.debug(
            f"Checking container measurements: Side 1: {side_one}, Side 2: {side_two}"
        )
        execute = True
        if side_one == 0.0 or side_two == 0.0:
            execute = False
        logging.debug(f"Container measurements valid: {execute}")
        return execute
