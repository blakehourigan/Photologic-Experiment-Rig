from tkinter import filedialog
import pandas as pd #type: ignore
import numpy as np #type: ignore 
import tkinter as tk
from collections import defaultdict

from typing import Tuple, List

import random

class DataManager:
    def __init__(self, controller) -> None:
        self.controller = controller

        self.stimuli_dataframe = pd.DataFrame()
        self.licks_dataframe = pd.DataFrame()
        
        self.stimuli_vars = {f"Valve {i+1} substance": tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)

        # initialize lists to hold original pairs and the list that will hold our dataframes.

        self.pairs: list[Tuple] = []

        # Initialize variables that will keep track of the total number of trials we will have, the total number of trial blocks that the user wants to run
        # and the total number of stimuli. These are of type IntVar because they are used in the GUI.

        self.num_trials = tk.IntVar(value=0)
        self.num_trial_blocks = tk.IntVar(value=4)
        self.num_stimuli = tk.IntVar(value=4)
        self.TTC_lick_threshold = tk.IntVar(value=3)

        # initializing variable for iteration through the trials in the program

        self.current_trial_number = 1

        self.current_iteration = 0
            
        self.interval_vars = {
            "ITI_var": tk.IntVar(value=30000),
            "TTC_var": tk.IntVar(value=15000),
            "sample_var": tk.IntVar(value=15000),
            "ITI_random_entry": tk.IntVar(value=5000),
            "TTC_random_entry": tk.IntVar(value=5000),
            "sample_random_entry": tk.IntVar(value=5000),
        }

        # initializing the lists that will hold the final calculated random interval values

        self.ITI_intervals_final: list[int] = []
        self.TTC_intervals_final: list[int] = []
        self.sample_intervals_final: list[int] = []

        # Initialize the time, licks to 0

        self.start_time = 0.0
        self.state_start_time = 0.0

        self.side_one_licks = 0
        self.side_two_licks = 0
        self.total_licks = 0

        self.blocks_generated = False

    def initialize_stimuli_dataframe(self) -> None:
        """filling the dataframe with the values that we have at this time"""
        if hasattr(self, "stimuli_dataframe"):
            del self.stimuli_dataframe

        self.create_trial_blocks()
        stimuli_1, stimuli_2 = self.generate_pairs()

        block_size = int(self.num_stimuli.get() / 2)
        data = {
            "Trial Block": np.repeat(
                range(1, self.controller.data_mgr.num_trial_blocks.get() + 1),
                block_size,
            ),
            "Trial Number": np.repeat(range(1, self.num_trials.get() + 1), 1),
            "Port 1": stimuli_1,
            "Port 2": stimuli_2,
            "Port 1 Licks": np.full(self.num_trials.get(), np.nan),
            "Port 2 Licks": np.full(self.num_trials.get(), np.nan),
            "ITI": self.ITI_intervals_final,
            "TTC": self.TTC_intervals_final,
            "Sample Time": self.sample_intervals_final,
            "TTC Actual": np.full(self.num_trials.get(), np.nan),
        }

        df = pd.DataFrame(data)

        self.stimuli_dataframe = df

        self.blocks_generated = True
        self.controller.program_schedule_window.show_stimuli_table()
        self.controller.arduino_mgr.send_schedule_to_motor()

    def create_trial_blocks(self):
        """this is the function that will generate the full roster of stimuli for the duration of the program"""

        # the total number of trials equals (number stimuli / 2) because each stimuli is paired up, times the number of trial blocks that we want
        self.num_trials.set(((self.num_stimuli.get() / 2) * self.num_trial_blocks.get()))

        max_time = self.create_random_intervals()

        minutes, seconds = self.controller.main_gui.convert_seconds_to_minutes_seconds(max_time / 1000)  # converting our max runtime in ms to max time in minues, seconds format
        self.controller.main_gui.update_max_time(minutes, seconds)
        """this checks every variable in the simuli_vars dictionary against the default value, if it is changed, then it is added to the list 
                            var for iterator, (key, value) in enumerate(self.stimuli_vars.items() if variable not default then add to list)"""
        self.changed_vars = [
            stimulus
            for i, (key, stimulus) in enumerate(
                self.stimuli_vars.items()
            )  # for each key and value in stimuli_vars, check if the value is the default value, if not add it to changed list
            if stimulus.get()
            != f"Valve {i+1} substance"  # f string used to incorporate var in string
        ]

        # Handling the case that you generate the plan for a large num of stimuli and then change to a smaller number
        if len(self.changed_vars) > self.num_stimuli.get():
            # Start at the number of stimuli you now have
            start_index = self.num_stimuli.get()
            # and then set the rest of stimuli past that value back to default to avoid error
            # create an index for each loop, loop through each key in stimuli_vars
            for index, key in enumerate(self.stimuli_vars):
                if index >= start_index:
                    # if the loop we are on is greater than the start index calculated, then set the value to the value held by the key.
                    self.stimuli_vars[key].set(key)

        # from our list of variables that were changed from their default values, pair them together in a new pairs list.
        # 1 is paired with 2. 3 with 4, etc

        def get_paired_index(i, total_entries):
            if total_entries == 2:
                # If there are only two entries, pair them directly
                return 1 - i  # This will swap 0 with 1 and 1 with 0
            elif total_entries == 4:
                # For 4 entries, pair 1 with 4 (0 with 3) and 2 with 3 (1 with 2)
                return total_entries - i - 1
            elif total_entries == 8:
                # For 8 entries, the pattern is a bit more complex
                if i % 2 == 0:  # even index (0 or 2)
                    return (
                        i + 5
                    ) % total_entries  # Pair 1 (0) with 6 (5) and 3 (2) with 8 (7)
                else:  # odd index (1 or 3)
                    return (
                        i + 3
                    ) % total_entries  # Pair 2 (1) with 5 (4) and 4 (3) with 7 (6)
            else:
                raise ValueError("Unexpected number of entries")

        if self.changed_vars:
            self.pairs = []
            total_entries = len(self.changed_vars)  # Can be 2, 4, or 8

            # Loop through the first half of the entries for pairing
            for i in range(total_entries // 2):
                pair_index = get_paired_index(i, total_entries)
                self.pairs.append((self.changed_vars[i], self.changed_vars[pair_index]))

        else:
            # if a stimulus has not been changed, this error message will be thrown to tell the user to change it and try again.
            self.controller.main_gui.display_error(
                "Stimulus Not Changed",
                "One or more of the default stimuli have not been changed, please change the default value and try again",
            )

    def create_random_intervals(self) -> int:
        # clearing the lists here just in case we have already generated blocks, in this case we want to ensure we use new numbers, so we must clear out the existing ones
        self.ITI_intervals_final.clear()
        self.TTC_intervals_final.clear()
        self.sample_intervals_final.clear()

        # Assuming 'num_entries' is the number of entries (rows) you need to process
        for entry in range(self.num_trials.get()):
            for interval_type in ["ITI", "TTC", "sample"]:
                random_entry_key = f"{interval_type}_random_entry"
                var_key = f"{interval_type}_var"
                final_intervals_key = f"{interval_type}_intervals_final"

                # Generate a random interval
                random_interval = random.randint(
                    -self.interval_vars[random_entry_key].get(),
                    self.interval_vars[random_entry_key].get(),
                )

                # Calculate the final interval by adding the random interval to the state constant
                final_interval = self.interval_vars[var_key].get() + random_interval

                # Append the final interval to the corresponding list
                if not hasattr(self, final_intervals_key):
                    setattr(self, final_intervals_key, [])
                getattr(self, final_intervals_key).append(final_interval)

        max_time = (
            sum(self.ITI_intervals_final)
            + sum(self.TTC_intervals_final)
            + sum(self.sample_intervals_final)
        )

        return max_time
    
    def generate_pairs(self) -> Tuple[list, list]:
        pseudo_random_lineup: List[tuple] = []
        stimulus_1: List[str] = []
        stimulus_2: List[str] = []
        first_pair_counts: dict[tuple, int] = defaultdict(int)  # Dictionary to count first pairs
        consecutive_streaks: dict[int, int] = defaultdict(int)  # New dictionary to count streak lengths
        last_first_pair = None
        current_streak = 0

        for _ in range(self.num_trial_blocks.get()):
            if self.num_trial_blocks.get() != 0 and self.changed_vars:
                pairs_copy = [tuple(pair) for pair in self.pairs]
                random.shuffle(pairs_copy)  # Shuffle instead of picking one by one
                pseudo_random_lineup.extend(pairs_copy)
                first_pair_strings = tuple(var.get() for var in pairs_copy[0])
                first_pair_counts[first_pair_strings] += 1

                # New logic for tracking consecutive streaks
                if first_pair_strings == last_first_pair:
                    current_streak += 1
                else:
                    if current_streak > 0:
                        consecutive_streaks[current_streak] += 1
                    current_streak = 1
                    last_first_pair = first_pair_strings

            # Error handling remains unchanged
            elif len(self.changed_vars) == 0 and self.controller:
                self.controller.main_gui.display_error("Stimuli Variables Not Yet Changed",
                                                      "Stimuli variables have not yet been changed, to continue please change defaults and try again.")
            elif self.num_trial_blocks.get() == 0 and self.controller:
                self.controller.main_gui.display_error("Number of Trial Blocks 0",
                                                      "Number of trial blocks is currently still set to zero, please change the default value and try again.")

        # Handling the last streak
        if current_streak > 0:
            consecutive_streaks[current_streak] += 1

        # Unpack the pairs_shuffled list into two lists, one for each stimulus
        for entry in pseudo_random_lineup:
            stimulus_1.append(entry[0].get())
            stimulus_2.append(entry[1].get())

        # Calculate the percentage of each pair being first
        first_pair_percentages = {pair: count / self.num_trial_blocks.get() * 100 for pair, count in first_pair_counts.items()}
        print("Percentages of each pair appearing first:")
        for pair, percentage in first_pair_percentages.items():
            print(f"{pair}: {percentage:.2f}%")

        # Printing consecutive streaks
        print("\nConsecutive streaks of first pairs:")
        for streak_length, count in consecutive_streaks.items():
            print(f"Streak of {streak_length}: {count} times")

        return stimulus_1, stimulus_2


    def initalize_licks_dataframe(self):
        """setup the licks data frame that will hold the timestamps for the licks and which port was licked
        and create an empty first row to avoid a blank table when the program is first run
        """
        self.licks_dataframe = pd.DataFrame(
            [np.nan], columns=["Trial Number", "Port Licked", "Time Stamp"]
        )

    def save_licks(self, iteration):
        """define method that saves the licks to the data table and increments our iteration variable."""
        # if we get to this function straight from the TTC function, then we used up the full TTC and set TTC actual for this trial to the predetermined value
        command = "E"  # stop opening the valves on lick detection.
        self.controller.arduino_mgr.send_command_to_laser(command)
        
        
        if self.controller.state == "TTC":
            self.stimuli_dataframe.loc[
                self.current_trial_number - 1, "TTC Actual"
            ] = self.stimuli_dataframe.loc[self.current_trial_number - 1, "TTC"]
        

        # increment the trial number
        self.current_trial_number += 1

        # tell the motor to both increment the trial number and lift the door
        command = "<U>"                             
        self.controller.arduino_mgr.send_command_to_motor(command)
                
        # store licks in the ith rows in their respective stimuli column in the data table for the trial
        self.stimuli_dataframe.loc[iteration, "Port 1 Licks"] = self.side_one_licks
        self.stimuli_dataframe.loc[iteration, "Port 2 Licks"] = self.side_two_licks

        # this is how processes that are set to execute after a certain amount of time are cancelled.
        # call the self.master.after_cancel function and pass in the ID that was assigned to the function call

        # Jump to ITI state to begin ITI for next trial by incrementing the i variable
        self.controller.initial_time_interval(iteration + 1)

    def check_dataframe_entry_isfloat(self, iteration, state) -> int:
        """Method to check if the value in the dataframe is a numpy float. If it is, then we return the value. If not, we return -1."""
        interval_value = self.stimuli_dataframe.loc[iteration, state]

        # First, ensure that the retrieved value is not a DataFrame or Series
        if isinstance(interval_value, (pd.DataFrame, pd.Series)):
            return -1

        # Now that we're sure value is not a DataFrame or Series, check its type
        if isinstance(interval_value, (int, np.integer)):
            return int(interval_value)
        else:
            return -1

    def save_data_to_xlsx(self) -> None:
        # method that brings up the windows file save dialogue menu to save the two data tables to external files
        if not self.blocks_generated:
            self.controller.main_gui.display_error(
                "Blocks Not Generated",
                "Experiment blocks haven't been generated yet, please generate trial blocks and try again",
            )
        else:
            file_name = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile="lineup",
                title="Save Excel file",
            )

            self.stimuli_dataframe.to_excel(file_name, index=False)

            licks_file_name = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile="lineup",
                title="Save Excel file",
            )

            self.licks_dataframe.to_excel(licks_file_name, index=False)

    def pair_stimuli(self, stimulus_1, stimulus_2):
        """Preparing to send the data to the motor arduino"""
        paired_stimuli = list(zip(stimulus_1, stimulus_2))
        return paired_stimuli

    def reset_all(self):
        # Reset or clear all internal state that could persist
        self.stimuli_dataframe = pd.DataFrame()
        self.licks_dataframe = pd.DataFrame()
        self.stimuli_vars = {f"Valve {i+1} substance": tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)  # Reset to default

        self.pairs.clear()
        self.current_trial_number = 1
        self.ITI_intervals_final.clear()
        self.TTC_intervals_final.clear()
        self.sample_intervals_final.clear()

        # Reset numeric and boolean attributes as necessary
        self.num_trials.set(0)
        self.num_trial_blocks.set(4)
        self.num_stimuli.set(4)
        self.TTC_lick_threshold.set(3)

        # Add similar resets for any other relevant attributes

        self.blocks_generated = False

    def insert_trial_start_stop_into_licks_dataframe(self, motor_timestamps):
        print(motor_timestamps)
        arduino_start = next((entry for entry in motor_timestamps if entry["trial_number"] == 1 and entry["command"] == '0'), None)
        arduino_start = arduino_start['occurrence_time']
        time_offset = self.start_time - arduino_start

        for dictionary in motor_timestamps:
            if dictionary["command"] == 'U':
                state_label = "MOTOR UP"
            elif dictionary["command"] == 'D':
                state_label = "MOTOR DOWN"
            else:
                state_label = "something else"
            occurance_time = (dictionary['occurrence_time'] + time_offset) - self.start_time
            trial = dictionary["trial_number"]

            trial_entry = pd.Series([trial, "NONE", occurance_time / 1000, state_label], index=self.licks_dataframe.columns)

            self.licks_dataframe = pd.concat([self.licks_dataframe, trial_entry.to_frame().T], ignore_index=True)

        # Sort the DataFrame bed on the "Time Stamp" column
        self.licks_dataframe = self.licks_dataframe.sort_values(by="Time Stamp")
        self.licks_dataframe = self.licks_dataframe.reset_index(drop=True)
        
    @property
    def blocks_generated(self):
        return self._blocks_generated

    @blocks_generated.setter
    def blocks_generated(self, value):
        # You can add validation or additional logic here
        self._blocks_generated = value
