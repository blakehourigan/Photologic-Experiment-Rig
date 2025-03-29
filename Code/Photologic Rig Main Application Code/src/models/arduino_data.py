"""
This module defines the ArduinoData class, responsible for storing
data related to the Arduino controller that persists over different sesssions,
primarily valve open durations and experimental schedule information.

It handles loading and saving valve timing profiles (including archiving) to a
TOML configuration file at the current user's `Documents/Photologic-Experiment-Rig-Files` directory.

It also processes incoming data strings from the Arduino
during an experiment, parsing lick events and motor movements, and recording
them into the main experiment data structure (`ExperimentProcessData`). Relies on
`system_config` to locate configuration files and interacts with an `ExperimentProcessData`
instance passed during initialization.
"""

import logging
import datetime
import copy
from typing import Callable
import toml
import numpy as np
import numpy.typing as npt
from models.event_data import EventData
import system_config

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    ###TYPE HINTING###
    from models.experiment_process_data import ExperimentProcessData
    ###TYPE HINTING###

# Get the logger in use for the app
logger = logging.getLogger()

rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_POSSIBLE_VALVES = VALVE_CONFIG["TOTAL_POSSIBLE_VALVES"]
VALVES_PER_SIDE = TOTAL_POSSIBLE_VALVES // 2


class ArduinoData:
    """
    Manages Arduino-related data, focusing on valve duration storage persistence and
    processing incoming serial data during experiments.

    This class acts as an interface for saving and retrieving valve open durations
    from the TOML configuration file, implementing a simple archival and 'profile' system. It also
    contains methods to interpret data strings sent from the Arduino (like lick
    events and motor status) and record relevant information into an associated
    ExperimentProcessData pandas dataframe.

    Attributes
    ----------
    - **`exp_data`** (*ExperimentProcessData*): A reference to the main experiment data object, used for accessing schedule information and recording processed events.

    Methods
    -------
    - `find_first_not_filled`(...)
        Helper method to find the first available archive slot in the durations TOML file.
    - `save_durations`(...)
        Saves provided valve durations (side_one, side_two) either as the 'selected' profile or into an archive slot.
    - `load_durations`(...)
        Loads a specified valve duration profile (defaulting to 'selected') from the TOML file.
    - `load_schedule_indices`()
        Generates 0-indexed numpy arrays representing the valve schedule for an experiment based on `ExperimentProcessData` program_schedule_df.
    - `increment_licks`(...)
        Increments the appropriate lick counter in the `ExperimentProcessData`.
    - `handle_licks`(...)
        Parses and processes data strings specifically identified as lick events.
    - `record_event`(...)
        Records a processed event (lick or motor movement) into the `ExperimentProcessData` DataFrame.
    - `process_data`(...)
        Main entry point for parsing incoming data strings from the Arduino, routing to specific handlers (like `handle_licks`) based on content.
    """

    def __init__(self, exp_data):
        """
        Initializes the ArduinoData manager.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): The instance of the ExperimentProcessData class holding all current experiment configuration and trial data.
        """
        self.exp_data = exp_data

    def find_first_not_filled(self, toml_file: dict) -> int:
        """
        Searches the loaded TOML file structure for the first available archive slot.

        Checks `archive_1`, `archive_2`, then `archive_3` for attribute `filled = false`.

        Parameters
        ----------
        - **toml_file** (*dict*): The dictionary representation of the loaded valve durations TOML file.

        Returns
        -------
        - *int*: The index (1, 2, or 3) of the first unfilled archive slot. Returns 0 if all slots (1, 2, 3) are marked as filled.
        """
        first_available = 0

        for i in range(1, 4):
            archive = toml_file[f"archive_{i}"]
            if archive["filled"]:
                continue
            else:
                first_available = i
        return first_available

    def save_durations(
        self,
        side_one: npt.NDArray[np.int32],
        side_two: npt.NDArray[np.int32],
        type_durations: str,
    ) -> None:
        """
        Saves valve open durations to the `valve_durations.toml` configuration file.

        This function handles saving durations either as the primary 'selected' profile
        or archiving them. When archiving, it implements a FIFO (First-In, First-Out)
        logic using three archive slots:
        1. If slot 1 is free, save there.
        2. If slot 1 is full but 2 is free, move 1->2, save new to 1.
        3. If slots 1 and 2 are full (or all slots are full), move 2->3 (overwriting 3 if necessary), move 1->2, save new to 1.

        Converts NumPy arrays to Python lists before saving to TOML for compatibility reasons. Records the
        current datetime for the saved profile to mark when the profile was created.

        Parameters
        ----------
        - **side_one** (*npt.NDArray[np.int32]*): Numpy array of durations (microseconds) for side one valves.
        - **side_two** (*npt.NDArray[np.int32]*): Numpy array of durations (microseconds) for side two valves.
        - **type_durations** (*str*): Specifies the save location. Must be either `"selected"` (to update the main profile) or `"archive"`
        (to save to the next available archive slot).

        Raises
        ------
        - *FileNotFoundError*: If the `valve_durations.toml` file cannot be found at the path specified by `system_config`.
        - *toml.TomlDecodeError*: If the TOML file is malformed.
        - *IOError*: If there are issues reading or writing the TOML file.
        - *KeyError*: If the expected keys (`selected_durations`, `archive_1`, etc.) are missing in the TOML structure.
        """

        dur_path = system_config.get_valve_durations()

        with open(dur_path, "r") as f:
            toml_file = toml.load(f)

        if type_durations == "selected":
            selected_durations = toml_file["selected_durations"]

            # toml only knows how to deal with python native types (list, int, etc)
            # so we convert np arrays to lists
            selected_durations["date_used"] = datetime.datetime.now()
            selected_durations["side_one_durations"] = side_one.tolist()
            selected_durations["side_two_durations"] = side_two.tolist()

            # save the file with the updated content
            with open(dur_path, "w") as f:
                toml.dump(toml_file, f)
        elif type_durations == "archive":
            # find first archive not filled
            first_avail = self.find_first_not_filled(toml_file)

            match first_avail:
                case 1:
                    # 1 is available just insert
                    archive = toml_file["archive_1"]

                    archive["filled"] = True
                    archive["date_used"] = datetime.datetime.now()
                    archive["side_one_durations"] = side_one.tolist()
                    archive["side_two_durations"] = side_two.tolist()

                    with open(dur_path, "w") as f:
                        toml.dump(toml_file, f)
                case 2:
                    # move 1-> 2, insert 1
                    toml_file["archive_2"] = copy.deepcopy(toml_file["archive_1"])

                    archive_1 = toml_file["archive_1"]

                    archive_1["filled"] = True
                    archive_1["date_used"] = datetime.datetime.now()
                    archive_1["side_one_durations"] = side_one.tolist()
                    archive_1["side_two_durations"] = side_two.tolist()

                    with open(dur_path, "w") as f:
                        toml.dump(toml_file, f)

                case 3 | 0:
                    # case 3) 2 -> 3, 1-> 2, insert 1
                    # case 0 (no available archives) ) del / overwrite 3 (oldest), 2 -> 3, 1-> 2, insert 1
                    toml_file["archive_3"] = copy.deepcopy(toml_file["archive_2"])
                    toml_file["archive_2"] = copy.deepcopy(toml_file["archive_1"])

                    archive_1 = toml_file["archive_1"]

                    archive_1["filled"] = True
                    archive_1["date_used"] = datetime.datetime.now()
                    archive_1["side_one_durations"] = side_one.tolist()
                    archive_1["side_two_durations"] = side_two.tolist()

                    with open(dur_path, "w") as f:
                        toml.dump(toml_file, f)

    def load_durations(
        self, type_durations="selected_durations"
    ) -> tuple[npt.NDArray[np.int32], npt.NDArray[np.int32], datetime.datetime]:
        """
        Loads a specific valve duration profile from the `valve_durations.toml` file.

        Retrieves the durations for side one and side two, along with the timestamp
        when that profile was created. Converts the lists from the TOML file back
        into NumPy `np.int32` arrays for efficient operations.

        Parameters
        ----------
        - **type_durations** (*str, optional*): The key corresponding to the desired profile in the TOML file
        (e.g., `"selected_durations"`, `"default_durations"`, `"archive_1"`). Defaults to `"selected_durations"`.

        Returns
        -------
        - *tuple[npt.NDArray[np.int32], npt.NDArray[np.int32], datetime.datetime]*: A tuple containing:
            - Numpy array of durations for side one.
            - Numpy array of durations for side two.
            - The datetime object indicating when the loaded profile was saved.

        Raises
        ------
        - *FileNotFoundError*: If the `valve_durations.toml` file cannot be found.
        - *toml.TomlDecodeError*: If the TOML file is malformed.
        - *IOError*: If there are issues reading the TOML file.
        - *KeyError*: If the specified `type_durations` key or expected sub-keys (`side_one_durations`, `date_used`, etc.) are missing.
        """
        valve_durations_toml = system_config.get_valve_durations()

        with open(valve_durations_toml, "r") as f:
            toml_file = toml.load(f)

        file_durations = toml_file[type_durations]

        # create 2 np arrays 8 n long with np.int32s
        dur_side_one = np.full(VALVES_PER_SIDE, np.int32(0))
        dur_side_two = np.full(VALVES_PER_SIDE, np.int32(0))

        # keys here are names of durations i.e side_one_dur or side_two_dur, values
        # are lists of durations, VALVES_PER_SIDE long. Will produce two lists
        # VALVES_PER_SIDE long so that each valve in the rig is assigned a duration.
        for key, value in file_durations.items():
            if key == "side_one_durations":
                for i, duration in enumerate(value):
                    dur_side_one[i] = duration
            elif key == "side_two_durations":
                for i, duration in enumerate(value):
                    dur_side_two[i] = duration

        date_used = file_durations["date_used"]

        return dur_side_one, dur_side_two, date_used

    def load_schedule_indices(
        self,
    ) -> tuple[npt.NDArray[np.int8], npt.NDArray[np.int8]]:
        """
        Generates 0-indexed valve schedule arrays based on the experiment schedule.

        Uses the stimuli names and the trial-by-trial schedule defined in the
        associated `ExperimentProcessData` object (`self.exp_data`) to create two NumPy arrays.
        The index for side one is first found, then the associated valve is found via `exp_data.get_paired_index`.

        These arrays represent the 0-indexed valve number to be activated for each trial
        on side one and side two, respectively. This format is suitable for sending
        to the Arduino.

        Returns
        -------
        - *tuple[npt.NDArray[np.int8], npt.NDArray[np.int8]]*: A tuple containing:
            - Numpy array of 0-indexed valve numbers for side one schedule.
            - Numpy array of 0-indexed valve numbers for side two schedule.

        Raises
        ------
        - *AttributeError*: If `self.exp_data` or its required attributes/methods (like `stimuli_data`, `program_schedule_df`, `get_paired_index`) are missing or invalid.
        - *KeyError*: If expected keys (like 'Num Stimuli', 'Port 1') are missing in `exp_data`.
        - *ValueError*: If a stimulus name from the schedule is not found in the unique stimuli list.
        """
        stimuli_data = self.exp_data.stimuli_data
        schedule_df = self.exp_data.program_schedule_df

        num_stimuli = self.exp_data.exp_var_entries["Num Stimuli"]
        num_trials = self.exp_data.exp_var_entries["Num Trials"]

        sched_side_one = np.full(num_trials, np.int8(0))
        sched_side_two = np.full(num_trials, np.int8(0))

        # get unique stim names. this will give us all names on side one.
        # finding the index of a given stimuli appearing in a trial on side
        # one will easily allow us to find the paired index. We've already done
        # this before in exp_process_data
        names = list(stimuli_data.stimuli_vars.values())
        unique_names = names[: num_stimuli // 2]

        side_one_trial_stimuli = schedule_df["Port 1"].to_numpy()

        for i, trial_stim in enumerate(side_one_trial_stimuli):
            index = unique_names.index(trial_stim)
            sd_two_index = self.exp_data.get_paired_index(index, num_stimuli)
            sched_side_one[i] = index
            sched_side_two[i] = sd_two_index

        return sched_side_one, sched_side_two

    def increment_licks(self, side: int, event_data: EventData):
        """
        Increments the lick counter for the specified side within the EventData object.

        Parameters
        ----------
        - **side** (*int*): The side where the lick occurred (0 for side one, 1 for side two).
        - **event_data** (*EventData*): The EventData instance associated with `self.exp_data` where lick counts are stored.
        """
        match side:
            case 0:
                event_data.side_one_licks += 1
            case 1:
                event_data.side_two_licks += 1
            case _:
                logger.error("invalid side")

    def handle_licks(
        self,
        split_data: list[str],
        event_data: EventData,
        state: str,
        trigger: Callable,
    ) -> None:
        """
        Parses and records data specifically identified as a lick event.

        Extracts side, lick duration, timestamps, and valve duration (if in "SAMPLE" state)
        from the `split_data` list based on the current experiment `state` ("TTC" or "SAMPLE").
        Calls `increment_licks` and `record_event`. For "TTC" state, it checks if
        the lick count threshold is met to trigger a state change to "SAMPLE".

        Parameters
        ----------
        - **split_data** (*list[str]*): The list of strings resulting from splitting the incoming Arduino data by content separator '|'.
        - **event_data** (*EventData*): The EventData instance for accessing lick counts.
        - **state** (*str*): The current state of the experiment FSM (e.g., "TTC", "SAMPLE").
        - **trigger** (*Callable*): The state machine's trigger function, used here to transition state to "SAMPLE" state based on lick counts.

        Raises
        ------
        - *IndexError*: If `split_data` does not contain the expected number of elements for the given state.
        - *ValueError*: If elements in `split_data` cannot be converted to the expected types (int, np.int8, np.int32).
        """
        side = None
        valve_duration = None
        match state:
            case "TTC":
                # split_data will have the below form for ttc
                # 0(side)|67(duration)|6541(stamp_rel_to_start)|6541(stamp_rel_to_trial)
                # 1|16|0|496570|41 from arduino
                side = np.int8(split_data[0])
                self.increment_licks(side, event_data)

                lick_duration = np.int32(split_data[1])
                time_rel_to_start = np.int32(split_data[2]) / 1000
                time_rel_to_trial = np.int32(split_data[3]) / 1000

                # insert the values held in licks for respective sides in a shorter variable name
                side_one = self.exp_data.event_data.side_one_licks
                side_two = self.exp_data.event_data.side_two_licks
                # if 3 or more licks in a ttc time, jump straight to sample
                if side_one > 2 or side_two > 2:
                    trigger("SAMPLE")
                self.record_event(
                    side, lick_duration, time_rel_to_start, time_rel_to_trial, state
                )

            case "SAMPLE":
                try:
                    # 0|87|26064|8327|8327
                    side = np.int8(split_data[0])
                    self.increment_licks(side, event_data)

                    lick_duration = np.int32(split_data[1])
                    valve_duration = np.int32(split_data[2])
                    time_rel_to_start = np.int32(split_data[3]) / 1000
                    time_rel_to_trial = np.int32(split_data[4]) / 1000

                    self.record_event(
                        side,
                        lick_duration,
                        time_rel_to_start,
                        time_rel_to_trial,
                        state,
                        valve_duration,
                    )

                except Exception as e:
                    logging.error(f"IMPROPER DATA.... IGNORING.....{e}")

    def record_event(
        self,
        side: int,
        duration: np.int32,
        time_rel_to_start: float,
        time_rel_to_trial: float,
        state: str,
        valve_dur: np.int32 | None = None,
    ):
        """
        Records a processed event (lick or motor movement) into the `ExperimentProcessData` `EventData` DataFrame.

        Uses the `insert_row_into_df` method of the `EventData` object (`self.exp_data.event_data`)
        to add a new row containing the details of the event.

        Parameters
        ----------
        - **side** (*int*): The side associated with the event (0 for side one, 1 for side two).
        - **duration** (*np.int32*): The duration of the event (e.g., lick contact time) in milliseconds.
        - **time_rel_to_start** (*float*): The timestamp of the event relative to the start of the entire program, in seconds.
        - **time_rel_to_trial** (*float*): The timestamp of the event relative to the start of the current trial, in seconds.
        - **state** (*str*): A string describing the state during the event (e.g., "TTC", "SAMPLE").
        - **valve_dur** (*np.int32 | None, optional*): The duration the valve was open for this event (microseconds),
        if applicable (e.g., during "SAMPLE" state licks). Defaults to None.

        Raises
        ------
        - Propagates exceptions from `event_data.insert_row_into_df`.
        """
        try:
            event_data = self.exp_data.event_data
            current_trial = self.exp_data.current_trial_number
            # insert the lick record into the dataframe
            event_data.insert_row_into_df(
                current_trial,
                side + 1,
                duration,
                time_rel_to_start,
                time_rel_to_trial,
                state,
                valve_duration=(valve_dur if valve_dur else None),
            )

            logging.info(f"Lick data recorded for side: {side + 1}")
        except Exception as e:
            logging.error(f"Error recording lick data: {e}")
            raise

    def process_data(
        self, source: str, data: str, state: str, trigger: Callable
    ) -> None:
        """
        Processes incoming data strings received from the Arduino via the serial connection.

        Splits the raw data string by the '|' content separator. Determines the type of
        data based on the first element (`split_data[0]`). Directly handles "MOTOR" events,
        and routes lick data (`split_data[0]` is '0' or '1')
        to `handle_licks` for further processing.

        Parameters
        ----------
        - **source** (*str*): Identifier for the source of the data. Included for logging/debugging.
        - **data** (*str*): The raw data string received from the Arduino.
        - **state** (*str*): The current state of the experiment FSM, passed to handlers like `handle_licks`.
        - **trigger** (*Callable*): The state machine's trigger function, passed to handlers like `handle_licks`.

        Raises
        ------
        - *IndexError*: If `data.split('|')` results in an empty list or accessing `split_data[0]` fails.
        - Propagates exceptions from `handle_licks` or `record_event`.
        """
        event_data = self.exp_data.event_data
        split_data = data.split("|")
        try:
            if split_data[0] == "MOTOR":
                # data will arrive in the following format
                # MOTOR|DOWN|2338|7340|7340
                # MOTOR|MOVEMENT|DURATION|END_TIME_REL_TO_PROG_START|END_TIME_REL_TO_PROG_TRIAL_START
                event_data = self.exp_data.event_data

                current_trial = self.exp_data.current_trial_number

                event_data.insert_row_into_df(
                    current_trial,
                    None,
                    np.int32(split_data[2]),
                    (np.int32(split_data[3]) / 1000),
                    (np.int32(split_data[4]) / 1000),
                    f"MOTOR {split_data[1]}",
                )
            elif split_data[0] == "0" or split_data[0] == "1":
                self.handle_licks(split_data, event_data, state, trigger)

        except Exception as e:
            logging.error(f"Error processing data from {source}: {e}")
            raise
