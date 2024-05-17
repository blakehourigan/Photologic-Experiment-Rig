# data_manager.py
import logging
import json
from tkinter import filedialog
import pandas as pd
import numpy as np
import tkinter as tk
from collections import defaultdict
import traceback
import re
from typing import TYPE_CHECKING, Tuple, List

if TYPE_CHECKING:
    from program_control import ProgramController

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, controller: 'ProgramController') -> None:
        self.controller = controller
        self.stimuli_dataframe = pd.DataFrame()
        self.licks_dataframe = pd.DataFrame()
        
        self.stimuli_vars = {f"Valve {i+1} substance": tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)
        
        self.pairs: list[Tuple] = []
        self._num_trials = 0
        self._num_trial_blocks = tk.IntVar(value=10)
        self._num_stimuli = tk.IntVar(value=4)
        self._TTC_lick_threshold = tk.IntVar(value=3)
        self.current_trial_number = 1
        self.current_iteration = 0
        
        self.interval_vars = {
            "ITI_var": tk.IntVar(value=30000),
            "TTC_var": tk.IntVar(value=15000),
            "sample_var": tk.IntVar(value=15000),
            "ITI_random_entry": tk.IntVar(value=5000),
            "TTC_random_entry": tk.IntVar(value=0),
            "sample_random_entry": tk.IntVar(value=0),
        }

        self.ITI_intervals_final: list[int] = []
        self.TTC_intervals_final: list[int] = []
        self.sample_intervals_final: list[int] = []
        self.start_time = 0.0
        self.state_start_time = 0.0
        self.side_one_licks = 0
        self.side_two_licks = 0
        self.total_licks = 0
        self.blocks_generated = False
        self.side_one_trial_licks: list[list[float]] = []
        self.side_two_trial_licks: list[list[float]] = []




        self.write_to_json_file()
        
    def initialize_stimuli_dataframe(self) -> None:
        """filling the dataframe with the values that we have at this time"""
        logger.debug("Initializing stimuli dataframe.")
        if hasattr(self, "stimuli_dataframe"):
            del self.stimuli_dataframe

        self.create_trial_blocks()
        stimuli_1, stimuli_2 = self.generate_pairs()

        block_size = int(self.num_stimuli / 2)
        data = {
            "Trial Block": np.repeat(
                range(1, self.num_trial_blocks + 1),
                block_size,
            ),
            "Trial Number": np.repeat(range(1, self.num_trials + 1), 1),
            "Port 1": stimuli_1,
            "Port 2": stimuli_2,
            "Port 1 Licks": np.full(self.num_trials, np.nan),
            "Port 2 Licks": np.full(self.num_trials, np.nan),
            "ITI": self.ITI_intervals_final,
            "TTC": self.TTC_intervals_final,
            "Sample Time": self.sample_intervals_final,
            "TTC Actual": np.full(self.num_trials, np.nan),
        }

        df = pd.DataFrame(data)
        self.stimuli_dataframe = df
        self.blocks_generated = True
        self.send_data_to_motor()

    def send_data_to_motor(self) -> None:
        """Send a schedule to the motor Arduino and receive an echo for confirmation."""
        try:
            stim_var_list = list(self.stimuli_vars.values())
            filtered_stim_var_list = [item for item in stim_var_list if not re.match(r'Valve \d+ substance', item.get())]
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
                side_one_schedule = self.stimuli_dataframe['Port 1']
                side_two_schedule = self.stimuli_dataframe['Port 2']
                
                for i in range(len(side_one_schedule)):     
                    index = side_one_vars.index(side_one_schedule[i])
                    side_one_indexes.append(2 ** index)
                    index = side_two_vars.index(side_two_schedule[i])
                    side_two_indexes.append(2 ** index)

            self.arduino_data['last_used']['side_one_schedule'] = side_one_indexes
            self.arduino_data['last_used']['side_two_schedule'] = side_two_indexes
            
            # Convert the dictionary to a JSON string
            json_data = json.dumps(self.arduino_data['last_used'])

            # Create the command string
            arduino_command = 'A,' + json_data
            
            self.controller.send_command_to_arduino(arduino='motor', command=arduino_command)
                
            logger.info("Schedule sent to motor Arduino.")
        except Exception as e:
            logger.error(f"Error sending schedule to motor Arduino: {e}")
            error_message = traceback.format_exc()
            print(f"Error sending schedule to motor Arduino: {error_message}")
            self.controller.display_gui_error("Error sending schedule to motor Arduino:", str(e))
            raise

    def verify_arduino_schedule(self, side_one_indexes, side_two_indexes, verification):
        middle_index = len(verification) // 2
        side_one_verification_str = verification[:middle_index]
        side_two_verification_str = verification[middle_index:]
        side_one_verification = [int(x) for x in side_one_verification_str.split(',') if x.strip().isdigit()]
        side_two_verification = [int(x) for x in side_two_verification_str.split(',') if x.strip().isdigit()]
        
        are_equal_side_one = all(side_one_indexes[i] == side_one_verification[i] for i in range(len(side_one_indexes)))
        are_equal_side_two = all(side_two_indexes[i] == side_two_verification[i] for i in range(len(side_two_indexes)))
        
        if are_equal_side_one and are_equal_side_two:
            logger.info("Both lists are identical, Schedule Send Complete.")
        else:
            logger.warning("Lists are not identical.")
            self.controller.display_gui_error("Verification Error", "Lists are not identical.")

    def create_trial_blocks(self):
        """this is the function that will generate the full roster of stimuli for the duration of the program"""
        try:
            self.num_trials = (((self.num_stimuli // 2) * self.num_trial_blocks))
            max_time = self.create_random_intervals()
            minutes, seconds = self.controller.main_gui.convert_seconds_to_minutes_seconds(max_time / 1000)
            self.controller.main_gui.update_max_time(minutes, seconds)
            self.changed_vars = [
                stimulus
                for i, (key, stimulus) in enumerate(
                    self.stimuli_vars.items()
                )
                if stimulus.get() != f"Valve {i+1} substance"
            ]

            if len(self.changed_vars) > self.num_stimuli:
                start_index = self.num_stimuli
                for index, key in enumerate(self.stimuli_vars):
                    if index >= start_index:
                        self.stimuli_vars[key].set(key)

            def get_paired_index(i, total_entries):
                if total_entries == 2:
                    return 1 - i
                elif total_entries == 4:
                    return total_entries - i - 1
                elif total_entries == 8:
                    if i % 2 == 0:
                        return (i + 5) % total_entries
                    else:
                        return (i + 3) % total_entries
                else:
                    raise ValueError("Unexpected number of entries")

            if self.changed_vars:
                self.pairs = []
                total_entries = len(self.changed_vars)
                for i in range(total_entries // 2):
                    pair_index = get_paired_index(i, total_entries)
                    self.pairs.append((self.changed_vars[i], self.changed_vars[pair_index]))
            else:
                self.controller.display_gui_error(
                    "Stimulus Not Changed",
                    "One or more of the default stimuli have not been changed, please change the default value and try again",
                )
            logger.info("Trial blocks created.")
        except Exception as e:
            logger.error(f"Error creating trial blocks: {e}")
            raise

    def create_random_intervals(self) -> int:
        try:
            self.ITI_intervals_final.clear()
            self.TTC_intervals_final.clear()
            self.sample_intervals_final.clear()

            for entry in range(self.num_trials):
                for interval_type in ["ITI", "TTC", "sample"]:
                    random_entry_key = f"{interval_type}_random_entry"
                    var_key = f"{interval_type}_var"
                    final_intervals_key = f"{interval_type}_intervals_final"

                    random_interval = np.random.randint(
                        -self.interval_vars[random_entry_key].get(),
                        self.interval_vars[random_entry_key].get() + 1
                    )

                    final_interval = self.interval_vars[var_key].get() + random_interval

                    if not hasattr(self, final_intervals_key):
                        setattr(self, final_intervals_key, [])
                    getattr(self, final_intervals_key).append(final_interval)

            max_time = (
                sum(self.ITI_intervals_final)
                + sum(self.TTC_intervals_final)
                + sum(self.sample_intervals_final)
            )

            logger.info("Random intervals created.")
            return max_time
        except Exception as e:
            logger.error(f"Error creating random intervals: {e}")
            raise
    
    def generate_pairs(self) -> Tuple[list, list]:
        try:
            pseudo_random_lineup: List[tuple] = []
            stimulus_1: List[str] = []
            stimulus_2: List[str] = []
            first_pair_counts: dict[tuple, int] = defaultdict(int)
            consecutive_streaks: dict[int, int] = defaultdict(int)
            last_first_pair = None
            current_streak = 0

            for _ in range(self.num_trial_blocks):
                if self.num_trial_blocks != 0 and self.changed_vars:
                    pairs_copy = [tuple(pair) for pair in self.pairs]
                    np.random.shuffle(pairs_copy)
                    pseudo_random_lineup.extend(pairs_copy)
                    
                    first_pair_strings = tuple(var.get() for var in pairs_copy[0])
                    first_pair_counts[first_pair_strings] += 1

                    if first_pair_strings == last_first_pair:
                        current_streak += 1
                    else:
                        if current_streak > 0:
                            consecutive_streaks[current_streak] += 1
                        current_streak = 1
                        last_first_pair = first_pair_strings
                elif len(self.changed_vars) == 0 and self.controller:
                    self.controller.display_gui_error("Stimuli Variables Not Yet Changed",
                                                      "Stimuli variables have not yet been changed, to continue please change defaults and try again.")
            if current_streak > 0:
                consecutive_streaks[current_streak] += 1

            for entry in pseudo_random_lineup:
                stimulus_1.append(entry[0].get())
                stimulus_2.append(entry[1].get())

            first_pair_percentages = {pair: count / self.num_trial_blocks * 100 for pair, count in first_pair_counts.items()}
            logger.info("Percentages of each pair appearing first:")
            for pair, percentage in first_pair_percentages.items():
                logger.info(f"{pair}: {percentage:.2f}%")

            logger.info("\nConsecutive streaks of first pairs:")
            for streak_length, count in consecutive_streaks.items():
                logger.info(f"Streak of {streak_length}: {count} times")

            logger.info("Pairs generated.")
            return stimulus_1, stimulus_2
        except Exception as e:
            logger.error(f"Error generating pairs: {e}")
            raise

    def initalize_licks_dataframe(self):
        """setup the licks data frame that will hold the timestamps for the licks and which port was licked
        and create an empty first row to avoid a blank table when the program is first run
        """
        try:
            self.licks_dataframe = pd.DataFrame(
                [[np.nan, np.nan, np.nan]], columns=["Trial Number", "Licked Port", "Time Stamp"]
            )
            logger.info("Licks dataframe initialized.")
        except Exception as e:
            logger.error(f"Error initializing licks dataframe: {e}")
            raise

    def get_lick_timestamps(self, trial_number):
        """
        Returns a list of timestamps for the given trial number and licked port.
        """
        try:
            filtered_df_side_one = self.licks_dataframe[
                (self.licks_dataframe["Trial Number"] == trial_number)
                & (self.licks_dataframe["Licked Port"].isin([1.0]))
            ]
            filtered_df_side_two = self.licks_dataframe[
                (self.licks_dataframe["Trial Number"] == trial_number)
                & (self.licks_dataframe["Licked Port"].isin([2.0]))
            ]

            timestamps_side_one = filtered_df_side_one["Time Stamp"].tolist()
            timestamps_side_two = filtered_df_side_two["Time Stamp"].tolist()

            logger.info(f"Lick timestamps retrieved for trial {trial_number}.")
            return timestamps_side_one, timestamps_side_two
        except Exception as e:
            logger.error(f"Error getting lick timestamps for trial {trial_number}: {e}")
            raise

    def save_licks(self, iteration):
        """define method that saves the licks to the data table and increments our iteration variable."""
        try:
            command = "E"
            self.controller.send_command_to_arduino('laser', command)

            if self.controller.state == "TTC":
                self.stimuli_dataframe.loc[
                    self.current_trial_number - 1, "TTC Actual"
                ] = self.stimuli_dataframe.loc[self.current_trial_number - 1, "TTC"]

            self.current_trial_number += 1
            command = "<U>"                             
            self.controller.send_command_to_arduino('motor', command)
            
            self.stimuli_dataframe.loc[iteration, "Port 1 Licks"] = self.side_one_licks
            self.stimuli_dataframe.loc[iteration, "Port 2 Licks"] = self.side_two_licks

            self.controller.initial_time_interval(iteration + 1)
            logger.info(f"Licks saved for iteration {iteration}.")
        except Exception as e:
            logger.error(f"Error saving licks for iteration {iteration}: {e}")
            raise

    def check_dataframe_entry_isfloat(self, iteration, state) -> int:
        """Method to check if the value in the dataframe is a numpy float. If it is, then we return the value. If not, we return -1."""
        try:
            interval_value = self.stimuli_dataframe.loc[iteration, state]

            if isinstance(interval_value, (pd.DataFrame, pd.Series)):
                return -1

            if isinstance(interval_value, (int, np.integer)):
                return int(interval_value)
            else:
                return -1
        except Exception as e:
            logger.error(f"Error checking dataframe entry is float for iteration {iteration} and state {state}: {e}")
            raise
    def save_data_to_xlsx(self) -> None:
        """Method to bring up the windows file save dialog menu to save the two data tables to external files"""
        try:
            if not self.blocks_generated:
                self.controller.display_gui_error(
                    "Blocks Not Generated",
                    "Experiment blocks haven't been generated yet, please generate trial blocks and try again",
                )
            else:
                file_name = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel Files", "*.xlsx")],
                    initialfile="experiment schedule",
                    title="Save Excel file",
                )

                if file_name:
                    self.stimuli_dataframe.to_excel(file_name, index=False)
                else:
                    logger.info("User cancelled saving the stimuli dataframe.")

                licks_file_name = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel Files", "*.xlsx")],
                    initialfile="licks data",
                    title="Save Excel file",
                )

                if licks_file_name:
                    self.licks_dataframe.to_excel(licks_file_name, index=False)
                else:
                    logger.info("User cancelled saving the licks dataframe.")

            logger.info("Data saved to xlsx files.")
        except Exception as e:
            logger.error(f"Error saving data to xlsx: {e}")
            raise


    def pair_stimuli(self, stimulus_1, stimulus_2):
        """Preparing to send the data to the motor arduino"""
        try:
            paired_stimuli = list(zip(stimulus_1, stimulus_2))
            logger.info("Stimuli paired.")
            return paired_stimuli
        except Exception as e:
            logger.error(f"Error pairing stimuli: {e}")
            raise

    def reset_all(self):
        """Reset or clear all internal state that could persist"""
        try:
            self.stimuli_dataframe = pd.DataFrame()
            self.licks_dataframe = pd.DataFrame()
            self.stimuli_vars = {f"Valve {i+1} substance": tk.StringVar() for i in range(8)}
            for key in self.stimuli_vars:
                self.stimuli_vars[key].set(key)

            self.pairs.clear()
            self.current_trial_number = 1
            self.ITI_intervals_final.clear()
            self.TTC_intervals_final.clear()
            self.sample_intervals_final.clear()

            self.num_trials = 0
            self.num_trial_blocks = 4
            self.num_stimuli = 4
            self.TTC_lick_threshold = 3

            self.blocks_generated = False
            logger.info("All data reset.")
        except Exception as e:
            logger.error(f"Error resetting all data: {e}")
            raise

    def insert_trial_start_stop_into_licks_dataframe(self, motor_timestamps):
        try:
            arduino_start = next((entry for entry in motor_timestamps if entry["trial_number"] == 1 and entry["command"] == '0'), None)
            arduino_start = arduino_start['occurrence_time'] / 1000

            licks_columns = ["Trial Number", "Licked Port", "Time Stamp", "State"]
            trial_entries = []

            for dictionary in motor_timestamps:
                if dictionary["command"] == 'U':
                    state_label = "SIGNAL MOTOR UP"
                elif dictionary["command"] == 'D':
                    state_label = "SIGNAL MOTOR DOWN"
                elif dictionary["command"] == '0':
                    continue
                else:
                    state_label = dictionary["command"]

                occurrence_time = round((dictionary['occurrence_time'] / 1000), 3)
                trial = dictionary["trial_number"]
                trial_entry = pd.Series([trial, "NONE", occurrence_time, state_label], index=licks_columns)
                trial_entries.append(trial_entry)

            if self.licks_dataframe.empty:
                self.licks_dataframe = pd.DataFrame(trial_entries, columns=licks_columns)
            else:
                self.licks_dataframe = pd.concat([self.licks_dataframe, pd.DataFrame(trial_entries, columns=licks_columns)], ignore_index=True)

            self.licks_dataframe = self.licks_dataframe.sort_values(by="Time Stamp")
            self.licks_dataframe = self.licks_dataframe.reset_index(drop=True)
            logger.info("Trial start/stop timestamps inserted into licks dataframe.")
        except Exception as e:
            logger.error(f"Error inserting trial start/stop into licks dataframe: {e}")
            raise
    
    def initialize_arduino_json(self) -> None:
        # Define initial configuration data
        default_data = {
            "side_one_schedule": [],
            "side_two_schedule": [],
            "current_trial": 1,
            "valve_durations": [24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125]
        }

        last_used_data = {
            "side_one_schedule": [],
            "side_two_schedule": [],
            "current_trial": 1,
            "valve_durations": [25000, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125, 24125]
        }

        # Create a dictionary with named configurations
        self.arduino_data = {
            "default": default_data,
            "last_used": last_used_data
        }

        self.write_to_json_file()
    
    def write_to_json_file(self, filename='arduino_data.json'):
        with open(filename, 'w') as file:
            json.dump(self.arduino_data, file, indent=4)
    
    def read_json_file(filename='arduino_data.json'):
        with open(filename, 'r') as file:
            return json.load(file)
    
        # Function to load a specific configuration
    def load_configuration(self, filename, config_name):
        data = self.read_json_file(filename)
        if config_name in data:
            return data[config_name]
        else:
            raise ValueError(f"Configuration '{config_name}' not found in {filename}")

    # Function to save a specific configuration
    def save_configuration(self, filename, config_name, config_data):
        data = self.read_json_file(filename)
        data[config_name] = config_data
        self.write_to_json_file(data, filename)
        
    
    @property
    def num_trials(self):
        return self._num_trials
        
    @num_trials.setter
    def num_trials(self, value):
        self._num_trials = value
        
    @property 
    def num_trial_blocks(self):
        return self._num_trial_blocks.get()
        
    @num_trial_blocks.setter
    def num_trial_blocks(self, value):
        if value < 0:
            raise ValueError("Number of trial blocks cannot be negative.")
        self._num_trial_blocks.set(value)
        
    def get_num_trial_blocks_var(self) -> tk.IntVar:
        return self._num_trial_blocks
        
    @property
    def num_stimuli(self):
        return self._num_stimuli.get()

    @num_stimuli.setter
    def num_stimuli(self, value):
        if value < 0:
            raise ValueError("Number of stimuli cannot be negative.")
        self._num_stimuli.set(value)
        
    def get_num_stimuli_var_reference(self) -> tk.IntVar:
        return self._num_stimuli
        
    @property
    def blocks_generated(self):
        return self._blocks_generated

    @blocks_generated.setter
    def blocks_generated(self, value):
        self._blocks_generated = value
