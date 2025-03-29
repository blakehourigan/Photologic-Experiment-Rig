"""
This module defines the ExperimentProcessData class, which serves as the central
data management hub for the Photologic-Experiment-Rig application.

It aggregates references to other data-holding classes (`StimuliData`, `EventData`,
`ArduinoData`) and manages core experimental parameters like current trial,
state time durations, and the overall experiment schedule DataFrame. It provides
methods for generating the experimental schedule, updating parameters from the GUI,
calculating runtime, and saving collected data.
"""

import logging
from tkinter import filedialog
import numpy as np
import pandas as pd
from typing import Tuple, List
import datetime
from pathlib import Path

from models.stimuli_data import StimuliData
from models.event_data import EventData
from models.arduino_data import ArduinoData
from views.gui_common import GUIUtils

logger = logging.getLogger(__name__)


class ExperimentProcessData:
    """
    Central data management class for the behavioral experiment.

    This class acts as the primary container and manager for all data related
    to an ongoing experiment. It holds references to specialized data classes
    (`EventData`, `StimuliData`, `ArduinoData`) and maintains experiment-wide
    state variables, timing intervals, parameter entries (num_stimuli for example), and the generated
    program schedule (`program_schedule_df`). It performs the generation
    of the trial schedule and state intervals based on user inputs.

    Attributes
    ----------
    - **`start_time`** (*float*): Timestamp marking the absolute start of the program run.
    - **`trial_start_time`** (*float*): Timestamp marking the start of the current trial.
    - **`state_start_time`** (*float*): Timestamp marking the entry into the current FSM state.
    - **`current_trial_number`** (*int*): The 1-indexed number of the trial currently in progress or about to start.
    - **`event_data`** (*EventData*): Instance managing the DataFrame of recorded lick/motor events.
    - **`stimuli_data`** (*StimuliData*): Instance managing stimuli names and related information.
    - **`arduino_data`** (*ArduinoData*): Instance managing Arduino communication data (durations, schedule indices) and processing incoming Arduino messages.
    - **`ITI_intervals_final`** (*npt.NDArray[np.int64] | None*): Numpy array holding the calculated Inter-Trial Interval duration (ms) for each trial.
    None until schedule generated.
    - **`TTC_intervals_final`** (*npt.NDArray[np.int64] | None*): Numpy array holding the calculated Time-To-Contact duration (ms) for each trial.
    None until schedule generated.
    - **`sample_intervals_final`** (*npt.NDArray[np.int64] | None*): Numpy array holding the calculated Sample period duration (ms) for each trial.
    None until schedule generated.
    - **`TTC_LICK_THRESHOLD`** (*int*): The number of licks required during the TTC state to trigger an early transition to the SAMPLE state.
    - **`interval_vars`** (*dict[str, int]*): Dictionary storing base and random variation values (ms) for timing intervals (ITI, TTC, Sample), sourced from GUI entries.
    - **`exp_var_entries`** (*dict[str, int]*): Dictionary storing core experiment parameters (Num Trial Blocks, Num Stimuli), sourced from GUI entries.
    `Num Trials` is calculated based on these other values.
    - **`program_schedule_df`** (*pd.DataFrame*): Pandas DataFrame holding the generated trial-by-trial schedule, including stimuli presentation, calculated intervals,
    and placeholders for results. Initialized empty.

    Methods
    -------
    - `update_model`(...)
        Updates internal parameter dictionaries (`interval_vars`, `exp_var_entries`) based on changes from GUI input fields (tkinter vars).
    - `get_default_value`(...)
        Retrieves the default or current value for a given parameter name from internal dictionaries, used to populate GUI fields initially.
    - `generate_schedule`()
        Performs the creation of the entire experimental schedule, including intervals and stimuli pairings. Returns status.
    - `create_random_intervals`()
        Calculates the final ITI, TTC, and Sample intervals for each trial based on base values and randomization ranges.
    - `calculate_max_runtime`()
        Estimates the maximum possible runtime based on the sum of all generated intervals.
    - `create_trial_blocks`()
        Determines the unique pairs of stimuli presented within a single block based on the number of stimuli.
    - `generate_pairs`(...)
        Generates the pseudo-randomized sequence of stimuli pairs across all trials and blocks.
    - `build_frame`(...)
        Constructs the `program_schedule_df` DataFrame using the generated stimuli sequences and intervals.
    - `save_all_data`()
        Initiates the process of saving the schedule and event log DataFrames to Excel files.
    - `get_paired_index`(...)
        Static method to determine the 0-indexed valve number on the opposite side corresponding to a given valve index on side one.
    - `save_df_to_xlsx`(...)
        Static method to handle saving a pandas DataFrame to an .xlsx file using a file dialog.
    - `convert_seconds_to_minutes_seconds`(...)
        Static method to convert a total number of seconds into minutes and remaining seconds.
    """

    def __init__(self):
        """
        Initializes the ExperimentProcessData central data hub.

        Sets initial timestamps to 0.0, starts `current_trial_number` at 1.
        Instantiates `EventData`, `StimuliData`, and `ArduinoData` (passing self reference).
        Initializes interval arrays (`ITI_intervals_final`, etc.) to None.
        Sets the `TTC_LICK_THRESHOLD`.
        Defines default values for `interval_vars` and `exp_var_entries`.
        Initializes `program_schedule_df` as an empty DataFrame.
        """

        self.start_time: float = 0.0
        self.trial_start_time: float = 0.0
        self.state_start_time: float = 0.0

        # this number is centralized here so that all state classes can access and update it easily without
        # passing it through to each state every time a state change occurs
        self.current_trial_number: int = 1

        self.event_data = EventData()
        self.stimuli_data = StimuliData()
        self.arduino_data = ArduinoData(self)

        self.ITI_intervals_final = None
        self.TTC_intervals_final = None
        self.sample_intervals_final = None

        # this constant should be used in arduino_data to say how many licks moves to sample
        self.TTC_LICK_THRESHOLD: int = 3

        self.interval_vars: dict[str, int] = {
            "ITI_var": 30000,
            "TTC_var": 20000,
            "sample_var": 15000,
            "ITI_random_entry": 0,
            "TTC_random_entry": 5000,
            "sample_random_entry": 5000,
        }
        self.exp_var_entries: dict[str, int] = {
            "Num Trial Blocks": 10,
            "Num Stimuli": 4,
            "Num Trials": 0,
        }

        # include an initial definition of program_schedule_df here as a blank df to avoid type errors and to
        # make it clear that this is a class attriute
        self.program_schedule_df = pd.DataFrame()

    def update_model(self, variable_name: str, value: int | None) -> None:
        """
        Updates internal parameter dictionaries from GUI inputs.

        Checks if the `variable_name` corresponds to a key in `interval_vars` or
        `exp_var_entries` and updates the dictionary value if the provided `value`
        is not None.

        Parameters
        ----------
        - **variable_name** (*str*): The name identifier of the variable being updated (should match a dictionary key).
        - **value** (*int | None*): The new integer value for the variable, or None if the input was invalid/empty.
        """

        # if the variable name for the tkinter entry item that we are updating is
        # in the exp_data interval variables dictionary, update that entry
        # with the value in the tkinter variable
        if value is not None:
            if variable_name in self.interval_vars.keys():
                self.interval_vars[variable_name] = value
            elif variable_name in self.exp_var_entries.keys():
                # update other var types here
                self.exp_var_entries[variable_name] = value

    def get_default_value(self, variable_name: str) -> int:
        """
        Retrieves the current value associated with a parameter name.

        Searches `interval_vars` and `exp_var_entries` for the `variable_name`.
        Used primarily to populate GUI fields with their initial/default values.

        Parameters
        ----------
        - **variable_name** (*str*): The name identifier of the parameter whose value is requested.

        Returns
        -------
        - *int*: The integer value associated with `variable_name` in the dictionaries, or -1 if the name is not found.
        """
        if variable_name in self.interval_vars.keys():
            return self.interval_vars[variable_name]
        elif variable_name in self.exp_var_entries.keys():
            # update other var types here
            return self.exp_var_entries[variable_name]

        # couldn't find the value, return -1 as error code
        return -1

    def generate_schedule(self) -> bool:
        """
        Generates the complete pseudo-randomized experimental schedule.

        Calculates the total number of trials based on stimuli count and block count.
        Validates the number of stimuli. Calls helper methods:
        - `create_random_intervals`() to determine ITI, TTC, Sample times per trial.
        - `create_trial_blocks`() to define unique stimuli pairs that must occur per block.
        - `generate_pairs`() to create the trial-by-trial stimuli sequence.
        - `build_frame`() to assemble the final `program_schedule_df`.

        Returns
        -------
        - *bool*: `True` if schedule generation was successful, `False` if an error occurred (e.g., invalid number of stimuli).
        """
        try:
            # set number of trials based on number of stimuli, and number of trial blocks set by user
            num_stimuli = self.exp_var_entries["Num Stimuli"]

            if num_stimuli > 8 or num_stimuli < 2 or num_stimuli % 2 != 0:
                GUIUtils.display_error(
                    "NUMBER OF STIMULI EXCEEDS CURRENT MAXIMUM",
                    "Program is currently configured for a minumim of 2 and maximum of 8 TOTAL vavles. You must have an even number of valves. If more are desired, program configuration must be modified.",
                )
                return False

            num_trial_blocks = self.exp_var_entries["Num Trial Blocks"]

            self.exp_var_entries["Num Trials"] = (num_stimuli // 2) * num_trial_blocks

            self.create_random_intervals()

            pairs = self.create_trial_blocks()

            # stimuli_1 & stimuli_2 are lists that hold the stimuli to be introduced for each trial on their respective side
            stimuli_side_one, stimuli_side_two = self.generate_pairs(pairs)

            # args needed -> stimuli_1, stimuli_2
            # these are lists of stimuli for each trial, for each side respectivelyc:w
            self.build_frame(
                stimuli_side_one,
                stimuli_side_two,
            )
            return True

        except Exception as e:
            logger.error(f"Error generating program schedule {e}.")
            return False

    def create_random_intervals(self) -> None:
        """
        Calculates randomized ITI, TTC, and Sample intervals for all trials.

        For each interval type (ITI, TTC, Sample):
        - Retrieves the base duration and random variation range from `interval_vars`.
        - Creates a base array repeating the base duration for the total number of trials.
        - If random variation is specified, generates an array of random integers within the +/- range.
        - Adds the random variation array to the base array.
        - Stores the resulting final interval array in the corresponding class attribute (`ITI_intervals_final`, etc.).

        Raises
        ------
        - Propagates NumPy errors (e.g., during random number generation or array addition).
        - *KeyError*: If expected keys are missing from `interval_vars`.
        """
        try:
            num_trials = self.exp_var_entries["Num Trials"]

            final_intervals = [None, None, None]

            interval_keys = ["ITI_var", "TTC_var", "sample_var"]

            random_interval_keys = [
                "ITI_random_entry",
                "TTC_random_entry",
                "sample_random_entry",
            ]

            # for each type of interval (iti, ttc, sample), generate final interval times
            for i in range(len(interval_keys)):
                base_val = self.interval_vars[interval_keys[i]]
                # this makes an array that is n=num_trials length of base_val
                base_intervals = np.repeat(base_val, num_trials)

                # get plus minus value for this interval type
                random_var = self.interval_vars[random_interval_keys[i]]

                if random_var == 0:
                    # if there is no value to add/subtract randomly, continue on
                    final_intervals[i] = base_intervals

                else:
                    # otherwise make num_trials amount of random integers and add them to the final_intervals
                    random_interval_arr = np.random.randint(
                        -random_var, random_var, num_trials
                    )

                    final_intervals[i] = np.add(base_intervals, random_interval_arr)

            # assign results for respective types to the model for storage and later use
            self.ITI_intervals_final = final_intervals[0]
            self.TTC_intervals_final = final_intervals[1]
            self.sample_intervals_final = final_intervals[2]

            logger.info("Random intervals created.")
        except Exception as e:
            logger.error(f"Error creating random intervals: {e}")
            raise

    def calculate_max_runtime(self) -> tuple[int, int]:
        """
        Estimates the maximum possible experiment runtime in minutes and seconds.

        Sums all generated interval durations (ITI, TTC, Sample) across all trials.
        Converts the total milliseconds to seconds, then uses `convert_seconds_to_minutes_seconds`.

        Returns
        -------
        - *tuple[int, int]*: A tuple containing (estimated_max_minutes, estimated_max_seconds).
        """
        max_time = (
            sum(self.ITI_intervals_final)
            + sum(self.TTC_intervals_final)
            + sum(self.sample_intervals_final)
        )
        minutes, seconds = self.convert_seconds_to_minutes_seconds(max_time / 1000)
        return (minutes, seconds)

    def create_trial_blocks(self) -> List[tuple[str, str]]:
        """
        Determines the unique stimuli pairings within a single trial block.

        Calculates the number of pairs per block (`block_sz = num_stimuli / 2`).
        Iterates from `i = 0` to `block_sz - 1`. For each `i`, finds the
        corresponding paired valve index using `get_paired_index`. Appends the
        tuple of (stimulus_name_at_i, stimulus_name_at_paired_index) to a list.

        Returns
        -------
        - *List[tuple]*: A list of tuples, where each tuple represents a unique stimuli pairing (e.g., `[('Odor A', 'Odor B'), ('Odor C', 'Odor D')]`).

        Raises
        ------
        - Propagates errors from `get_paired_index`.
        - *KeyError*: If expected keys are missing from `exp_var_entries`.
        - *IndexError*: If calculated indices are out of bounds for `stimuli_data.stimuli_vars`.
        """
        try:
            # creating pairs list which stores all possible pairs
            pairs = []
            num_stimuli = self.exp_var_entries["Num Stimuli"]
            block_sz = num_stimuli // 2

            stimuli_names = list(self.stimuli_data.stimuli_vars.values())

            for i in range(block_sz):
                pair_index = self.get_paired_index(i, num_stimuli)
                pairs.append((stimuli_names[i], stimuli_names[pair_index]))

            return pairs
        except Exception as e:
            logger.error(f"Error creating trial blocks: {e}")
            raise

    def generate_pairs(self, pairs: list[tuple[str, str]]) -> Tuple[list, list]:
        """
        Generates the full, pseudo-randomized sequence of stimuli pairs for all trials.

        Repeats the following for the number of trial blocks specified:
        - Takes the list of unique `pairs` generated by `create_trial_blocks` that must be included in each block.
        - Shuffles this list randomly (`np.random.shuffle`).
        - Extends a master list `pseudo_random_lineup` (adds new list to that list) with the shuffled block.
        After creating the full sequence, separates it into two lists: one for the
        stimulus presented on side one each trial, and one for side two.

        Parameters
        ----------
        - **pairs** (*List[tuple[str, str]]*): The list of unique stimuli pairings defining one block, generated by `create_trial_blocks`.

        Returns
        -------
        - *Tuple[list, list]*: A tuple containing two lists:
            - `stimulus_1`: List of stimuli names for Port 1 for each trial.
            - `stimulus_2`: List of stimuli names for Port 2 for each trial.

        Raises
        ------
        - Propagates errors from `np.random.shuffle`.
        """
        try:
            pseudo_random_lineup: List[tuple] = []

            stimulus_1: List[str] = []
            stimulus_2: List[str] = []

            for _ in range(self.exp_var_entries["Num Trial Blocks"]):
                pairs_copy = [tuple(pair) for pair in pairs]
                np.random.shuffle(pairs_copy)
                pseudo_random_lineup.extend(pairs_copy)

            for pair in pseudo_random_lineup:
                stimulus_1.append(pair[0])
                stimulus_2.append(pair[1])

            return stimulus_1, stimulus_2
        except Exception as e:
            logger.error(f"Error generating pairs: {e}")
            raise

    def build_frame(
        self,
        stimuli_1: list[str],
        stimuli_2: list[str],
    ) -> None:
        """
        Constructs the main `program_schedule_df` pandas DataFrame.

        Uses the generated stimuli sequences (`stimuli_1`, `stimuli_2`) and the
        calculated interval arrays (`ITI_intervals_final`, etc.) to build the
        DataFrame. Includes columns for trial block number, trial number, stimuli
        per port, calculated intervals, and placeholders (NaN) for results columns
        like lick counts and actual TTC duration.

        Parameters
        ----------
        - **stimuli_1** (*list*): List of stimuli names for Port 1, one per trial.
        - **stimuli_2** (*list*): List of stimuli names for Port 2, one per trial.

        Raises
        ------
        - Propagates pandas errors during DataFrame creation.
        - *ValueError*: If the lengths of input lists/arrays do not match the expected number of trials.
        """
        num_stimuli = self.exp_var_entries["Num Stimuli"]
        num_trials = self.exp_var_entries["Num Trials"]
        num_trial_blocks = self.exp_var_entries["Num Trial Blocks"]

        # each block must contain each PAIR -> num pairs = num_stim / 2
        block_size = int(num_stimuli / 2)
        try:
            data = {
                "Trial Block": np.repeat(
                    range(1, num_trial_blocks + 1),
                    block_size,
                ),
                "Trial Number": np.repeat(range(1, num_trials + 1), 1),
                "Port 1": stimuli_1,
                "Port 2": stimuli_2,
                "Port 1 Licks": np.full(num_trials, np.nan),
                "Port 2 Licks": np.full(num_trials, np.nan),
                "ITI": self.ITI_intervals_final,
                "TTC": self.TTC_intervals_final,
                "SAMPLE": self.sample_intervals_final,
                "TTC Actual": np.full(num_trials, np.nan),
            }

            self.program_schedule_df = pd.DataFrame(data)

            logger.info("Initialized stimuli dataframe.")
        except Exception as e:
            logger.debug(f"Error Building Stimuli Frame: {e}.")
            raise

    def save_all_data(self):
        """
        Saves the experiment schedule and detailed event log DataFrames to Excel files.

        Iterates through a dictionary mapping descriptive names to the DataFrame
        references (`program_schedule_df`, `event_data.event_dataframe`) and calls
        the static `save_df_to_xlsx` method for each.
        """
        dataframes = {
            "Experiment Schedule": self.program_schedule_df,
            "Detailed Event Log Data": self.event_data.event_dataframe,
        }

        for name, df_reference in dataframes.items():
            self.save_df_to_xlsx(name, df_reference)

    @staticmethod
    def get_paired_index(i: int, num_stimuli: int) -> int | None:
        """
        Calculates the 0-indexed valve number for the stimulus for side two based on give index (i) for side one.

        Based on the total number of stimuli (`num_stimuli`), determines the index
        of the valve paired with the valve at index `i`. Handles cases for 2, 4, or 8 total stimuli.

        Parameters
        ----------
        - **i** (*int*): The 0-indexed number of the valve on one side.
        - **num_stimuli** (*int*): The total number of stimuli/valves being used (must be 2, 4, or 8).

        Returns
        -------
        - *int | None*: The 0-indexed number of the paired valve, or None if `num_stimuli` is not 2, 4, or 8.
        """
        match num_stimuli:
            case 2:
                # if num stim is 2, we are only running the same stimulus on both sides,
                # we will only see i=0 here, and its paired with its sibling i=4
                return i + 4
            case 4:
                # if num stim is 4, we are only running 2 stimuli per side,
                # we will see i=0 and i =1 here, paired with siblings i=5 & i=4 respectively
                match i:
                    case 0:  # valve 1
                        return i + 5  # (5) / valve 6
                    case 1:  # valve 2
                        return i + 3  # (4) / valve 5
            case 8:
                match i:
                    case 0:
                        return i + 5
                    case 1:
                        return i + 3
                    case 2:
                        return i + 5
                    case 3:
                        return i + 3
            case _:
                return None

    @staticmethod
    def save_df_to_xlsx(name: str, dataframe: pd.DataFrame) -> None:
        """
        Saves a pandas DataFrame to an Excel (.xlsx) file using a file save dialog.

        Prompts the user with a standard 'Save As' dialog window. Suggests a default
        filename including the provided `name` and the current date. Sets the default
        directory to '../data_outputs'. If the user confirms a filename, saves the
        DataFrame; otherwise, logs that the save was cancelled.

        Parameters
        ----------
        - **name** (*str*): A descriptive name used in the default filename (e.g., "Experiment Schedule").
        - **dataframe** (*pd.DataFrame*): The pandas DataFrame to be saved.

        Raises
        ------
        - Propagates errors from `filedialog.asksaveasfilename` or `dataframe.to_excel`.
        """
        try:
            file_name = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile=f"{name}, {datetime.date.today()}",
                initialdir=Path(__file__).parent.parent.parent.resolve()
                / "data_outputs",
                title="Save Excel file",
            )

            if file_name:
                dataframe.to_excel(file_name, index=False)
            else:
                logger.info("User cancelled saving the stimuli dataframe.")

            logger.info("Data saved to xlsx files.")
        except Exception as e:
            logger.error(f"Error saving data to xlsx: {e}")
            raise

    @staticmethod
    def convert_seconds_to_minutes_seconds(total_seconds: int) -> tuple[int, int]:
        """
        Converts a total number of seconds into whole minutes and remaining seconds.

        Parameters
        ----------
        - **total_seconds** (*int*): The total duration in seconds.

        Returns
        -------
        - *tuple[int, int]*: A tuple containing (minutes, seconds).

        Raises
        ------
        - Propagates `TypeError` if `total_seconds` is not a number.
        """
        try:
            # Integer division to get whole minutes
            minutes = total_seconds // 60
            # Modulo to get remaining seconds
            seconds = total_seconds % 60
            return minutes, seconds
        except Exception as e:
            logger.error(f"Error converting seconds to minutes and seconds: {e}")
            raise
