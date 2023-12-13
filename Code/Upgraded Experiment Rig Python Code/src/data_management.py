from tkinter import filedialog
import pandas as pd
import numpy as np
import random
import tkinter as tk
from typing import Tuple


class DataManager:
    def __init__(self, controller) -> None:
        self.controller = controller

        self.stimuli_dataframe = pd.DataFrame()
        self.licks_dataframe = pd.DataFrame()

        self.stimuli_vars = {f"stimuli_var_{i+1}": tk.StringVar() for i in range(8)}
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

    def create_trial_blocks(self):
        """this is the function that will generate the full roster of stimuli for the duration of the program"""

        # the total number of trials equals the number of stimuli times the number of trial blocks that we want
        self.num_trials.set((self.num_stimuli.get() * self.num_trial_blocks.get()))

        self.create_random_intervals()

        """this checks every variable in the simuli_vars dictionary against the default value, if it is changed, then it is added to the list 
                            var for iterator, (key, value) in enumerate(self.stimuli_vars.items() if variable not default then add to list)"""
        self.changed_vars = [
            v
            for i, (k, v) in enumerate(self.stimuli_vars.items())
            if v.get() != f"stimuli_var_{i+1}"
        ]
        # f string used to incorporate var in string
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
        if len(self.changed_vars) > 0:
            # increment by 2 every loop to avoid placing the same stimuli in the list twice
            self.pairs = [
                (self.changed_vars[i], self.changed_vars[i + 1])
                for i in range(0, len(self.changed_vars), 2)
            ]
        else:
            # if a stimulus has not been changed, this error message will be thrown to tell the user to change it and try again.
            self.controller.main_gui.display_error(
                "Stimulus Not Changed",
                "One or more of the default stimuli have not been changed, please change the default value and try again",
            )
        # for each pair in pairs list, include each pair flipped
        self.pairs.extend([(pair[1], pair[0]) for pair in self.pairs])

    def create_random_intervals(self) -> None:
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

    def generate_pairs(self) -> Tuple[list, list]:
        # if the user has changed the defualt values of num_blocks and changed variables, then generate the experiment schedule

        stimulus_1, stimulus_2, pairs_shuffled = [], [], []

        if self.num_trial_blocks.get() != 0 and len(self.changed_vars) > 0:
            for i in range(0, self.num_trial_blocks.get()):
                # Create a copy of the pairs
                pairs_copy = [
                    (var1.get(), var2.get()) for var1, var2 in self.pairs
                ]  # copy pairs list to pairs_copy

                # Shuffle the copy
                random.shuffle(
                    pairs_copy
                )  # shuffling all pairs for psudeo randomization

                pairs_shuffled.extend(
                    pairs_copy
                )  # add every pair in pairs copy to larger shuffled pairs list, after loop we have num_stimuli * num_trial_blocks pairs

            # Unpack the pairs_shuffled list into two lists, one for each stimulus
            for tuple in pairs_shuffled:
                stimulus_1.append(tuple[0])
                stimulus_2.append(tuple[1])

        elif len(self.changed_vars) == 0:
            self.controller.main_gui.display_error(
                "Stimuli Variables Not Yet Changed",
                "Stimuli variables have not yet been changed, to continue please change defaults and try again.",
            )

        elif self.controller.logic.num_trial_blocks.get() == 0:
            self.controller.main_gui.display_error(
                "Number of Trial Blocks 0",
                "Number of trial blocks is currently still set to zero, please change the default value and try again.",
            )

        return stimulus_1, stimulus_2

    def initialize_stimuli_dataframe(self) -> None:
        """filling the dataframe with the values that we have at this time"""
        if hasattr(self, "stimuli_dataframe"):
            del self.stimuli_dataframe

        self.create_trial_blocks()
        stimuli_1, stimuli_2 = self.generate_pairs()

        data = {
            "Trial Block": np.repeat(
                range(1, self.controller.data_mgr.num_trial_blocks.get() + 1),
                self.num_stimuli.get(),
            ),
            "Trial Number": np.repeat(range(1, self.num_trials.get() + 1), 1),
            "Stimulus 1": stimuli_1,
            "Stimulus 2": stimuli_2,
            "Stimulus 1 Licks": np.full(self.num_trials.get(), np.nan),
            "Stimulus 2 Licks": np.full(self.num_trials.get(), np.nan),
            "ITI": self.ITI_intervals_final,
            "TTC": self.TTC_intervals_final,
            "Sample Time": self.sample_intervals_final,
            "TTC Actual": np.full(self.num_trials.get(), np.nan),
        }

        df = pd.DataFrame(data)

        self.stimuli_dataframe = df

        self.blocks_generated = True
        self.controller.experiment_ctl_wind.show_stimuli_table()

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
        if self.controller.state == "TTC":
            self.stimuli_dataframe.loc[
                self.current_trial_number - 1, "TTC Actual"
            ] = self.stimuli_dataframe.loc[self.current_trial_number - 1, "TTC"]

            (
                stimulus_1_position,
                stimulus_2_position,
            ) = self.data_mgr.find_stimuli_positions(iteration)

            self.controller.arduino_mgr.close_valves(stimulus_1_position, stimulus_2_position)
            command = (
                "SIDE_ONE\n"
                + str(self.stim1_position)
                + "\nSIDE_TWO\n"
                + str(self.stim2_position)
                + "\n"
            )
            self.controller.arduino_mgr.send_command_to_motor(command)

        command = b"UP\n"
        # tell the motor arduino to move the door up
        self.controller.arduino_mgr.send_command_to_motor(command)

        # increment the trial number
        self.current_trial_number += 1

        # store licks in the ith rows in their respective stimuli column in the data table for the trial
        self.stimuli_dataframe.loc[iteration, "Stimulus 1 Licks"] = self.side_one_licks
        self.stimuli_dataframe.loc[iteration, "Stimulus 2 Licks"] = self.side_two_licks

        # this is how processes that are set to execute after a certain amount of time are cancelled.
        # call the self.master.after_cancel function and pass in the ID that was assigned to the function call
        self.controller.main_gui.root.after_cancel(
            self.controller.logic.update_licks_id
        )

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

    def find_stimuli_positions(self, i) -> tuple:
        # Create a list of the stimuli dictionary values, will give list of stimuli.
        stim_var_list = list(self.stimuli_vars.values())
        for index, string_var in enumerate(stim_var_list):
            if string_var.get() == self.stimuli_dataframe.loc[i, "Stimulus 1"]:
                self.stim1_position = str(index + 1)

            # repeat process for the second stimulus
            elif string_var.get() == self.stimuli_dataframe.loc[i, "Stimulus 2"]:
                self.stim2_position = str(index + 1)

        return self.stim1_position, self.stim2_position

    @property
    def blocks_generated(self):
        return self._blocks_generated

    @blocks_generated.setter
    def blocks_generated(self, value):
        # You can add validation or additional logic here
        self._blocks_generated = value
