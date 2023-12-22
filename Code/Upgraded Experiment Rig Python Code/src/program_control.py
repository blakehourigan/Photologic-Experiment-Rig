import tkinter as tk
import time

# Helper classes
from arduino_control import AduinoManager
from experiment_config import Config
from data_management import DataManager

# GUI classses
from main_gui import MainGUI
from data_window import DataWindow
from experiment_control_window import ExperimentCtlWindow
from licks_window import LicksWindow
from test_valves_window import valveTestWindow
from test_valves_logic import valveTestLogic 


class ProgramController:
    def __init__(self) -> None:
        self.config = Config()

        self.main_gui = MainGUI(self)
        self.data_window = DataWindow(self)
        self.licks_window = LicksWindow(self)
        self.experiment_ctl_wind = ExperimentCtlWindow(self)


        self.data_mgr = DataManager(self)
        self.arduino_mgr = AduinoManager(self)
        
        self.valve_testing_window = valveTestWindow(self)
        self.valve_test_logic = valveTestLogic(self)

        # Initialize running flag to false
        self.running = False
        self.state = "OFF"

        self.after_ids: list[str] = []

    def start_main_gui(self) -> None:
        """start the main GUI and connect to the arduino"""
        self.main_gui.setup_gui()
        self.arduino_mgr.connect_to_arduino()
        self.main_gui.root.mainloop()

    def initial_time_interval(self, iteration: int) -> None:
        """defining the ITI state method, arguments given are self which gives us access to class attributes and other class methods,
        the second argument is iteration, which is the iteration variable that we use to keep track of what trial we are on.
        """

        """ If we have pressed start, and the current trial number is less than the number of trials determined by number of stim * number of trial blocks, 
            then continue running through more trials"""

        if not self.data_mgr.blocks_generated:
            self.stop_program()
            self.main_gui.display_error(
                "Blocks not Generated",
                "Please generate blocks before starting the program.",
            )

        elif self.data_mgr.current_trial_number > (self.data_mgr.num_trials.get()):
            self.stop_program()  # if we have gone through every trial then end the program.

        elif self.running:
            self.state = "ITI"

            # new trial so reset the lick counters
            self.data_mgr.side_one_licks = 0
            self.data_mgr.side_two_licks = 0

            # configure the state time label in the top right of the main window to hold the value of the new state
            self.main_gui.state_time_label_header.configure(
                text=(self.state + " Time:")
            )

            # update the state start time to now, so that it starts at 0
            self.data_mgr.state_start_time = time.time()

            # Get trial number and stimuli in the trial and add them to the main information screen
            # self.df_stimuli.loc is what we use to get values that are held in the main data table. Accessed using .loc[row_num, 'Column Name']
            string = f'\nTRIAL # {self.data_mgr.current_trial_number}: Stimulus 1)  {self.data_mgr.stimuli_dataframe.loc[iteration, "Stimulus 1"]} vs. Stimulus 2)  {self.data_mgr.stimuli_dataframe.loc[iteration, "Stimulus 2"]}\n'

            # this command is what adds things to the main information screen
            self.main_gui.append_data(string)

            # for every letter in the string we just created, create a dash to separate the title of the trial from the contents
            for letter in range(len(string)):
                self.main_gui.append_data("-")

            # add the initial interval to the program information box
            ITI_Value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "ITI")

            self.main_gui.append_data(
                "\nInitial Interval Time: " + str(ITI_Value / 1000.0) + "s\n"
            )

            def callback():
                self.time_to_contact(iteration)

            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            self.main_gui.root.after(int(ITI_Value), callback)

    def time_to_contact(self, iteration: int):
        """defining the TTC state method, argument are self and iteration. iteration is passed from ITI to keep track of what stimuli we are on."""
        if self.running:
            """start reading licks, we pass the same i into this function that we used in the previous function to
            keep track of where we are storing the licks in the data table"""
            self.state = "TTC"

            self.read_licks(iteration)

            self.main_gui.state_time_label_header.configure(
                text=(self.state + " Time:")
            )  # update state timer header

            self.data_mgr.state_start_time = time.time()  # state start time begins

            command = "DOWN\n"  # tell motor arduino to move the door down
            self.arduino_mgr.send_command_to_motor(command)

            """ Look in the dataframe in the current trial for the stimulus to give, once found mark the index with corresponding solenoid
            valve number and save into stimulus position variables. """

            (
                stimulus_1_position,
                stimulus_2_position,
            ) = self.data_mgr.find_stimuli_positions(iteration)

            self.arduino_mgr.open_both_valves(stimulus_1_position, stimulus_2_position)
            
            TTC_Value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "TTC")

            # write the time to contact to the program information box
            self.main_gui.append_data(
                "Time to Contact: " + str(TTC_Value / 1000.0) + "s\n"
            )

            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            self.after_sample_id = self.main_gui.root.after(
                int(TTC_Value), lambda: self.data_mgr.save_licks(iteration)
            )
            self.after_ids.append(self.after_sample_id)

    def sample_time(self, iteration):
        """define sample time method, i is again passed to keep track of trial and stimuli"""
        if self.running:
            self.state = "Sample"

            # change the state time label accordingly
            self.main_gui.state_time_label_header.configure(
                text=(self.state + " Time:")
            )

            # Update the state start time to the current time
            self.state_start_time = time.time()

            sample_interval_value = self.data_mgr.check_dataframe_entry_isfloat(
                iteration, "Sample Time"
            )

            # Appending the sample time interval to the main text box
            self.main_gui.append_data(
                "Sample Time Interval: "
                + str(sample_interval_value / 1000.0)
                + "s\n\n\n"
            )

            # After the sample time specified in the ith row of the 'Sample Time' table, we will jump to the save licks function
            self.main_gui.root.after(
                int(sample_interval_value), lambda: self.data_mgr.save_licks(iteration)
            )

    def test_valves(self) -> None:
        self.valve_testing_window.show_window()

    def read_licks(self, i):
        """Define the method for reading data from the optical fiber Arduino"""
        # try to read licks if there is a arduino connected
        available_data, stimulus = self.controller.arduino_mgr.read_from_laser()

        if available_data:
            # send the lick data to the data frame
            self.send_lick_data_to_dataframe(stimulus)
        # Call this method again every 100 ms
        self.update_licks_id = self.controller.main_gui.root.after(
            100, lambda: self.read_licks(i)
        )
        self.controller.after_ids.append(self.update_licks_id)

    def send_lick_data_to_dataframe(self, stimulus):
        data_mgr = self.controller.data_mgr
        licks_dataframe = data_mgr.licks_dataframe
        total_licks = data_mgr.total_licks

        licks_dataframe.loc[total_licks, "Trial Number"] = data_mgr.current_trial_number

        licks_dataframe.loc[
            total_licks, "Port Licked"
        ] = stimulus  # Send which stimulus was licked on this lick
        licks_dataframe.loc[total_licks, "Time Stamp"] = (
            time.time() - data_mgr.start_time
        )

        licks_dataframe.loc[total_licks, "State"] = self.controller.state

        if stimulus == "Stimulus 1":
            self.controller.data_mgr.side_one_licks += 1
        elif stimulus == "Stimulus 2":
            self.controller.data_mgr.side_two_licks += 1
        self.controller.data_mgr.total_licks += 1

    def check_licks_above_TTC_threshold(self, iteration):
        """define method for checking licks during the TTC state"""
        # if we are in the TTC state and detect 3 or more licks from either side, then immediately jump to the sample time
        # state and continue the trial
        self.TTC_lick_threshold = self.controller.data_mgr.TTC_lick_threshold

        if (
            self.side_one_licks >= self.TTC_lick_threshold
            or self.side_two_licks >= self.TTC_lick_threshold
        ) and self.controller.state == "TTC":
            self.controller.data_mgr.stimuli_dataframe.loc[
                self.controller.data_mgr.current_trial_number - 1, "TTC Actual"
            ] = (time.time() - self.controller.data_mgr.state_start_time) * 1000

            self.controller.main_gui.root.after_cancel(self.controller.after_sample_id)
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.controller.sample_time(iteration)

    def start_button_handler(self) -> None:
        """Handle toggling the program to running/not running on click of the start/stop button"""
        if self.running:
            self.stop_program()
        else:
            self.start_program()

    def clear_button_handler(self) -> None:
        """Handle clearing the data window on click of the clear button"""
        elapsed_time, state_elapsed_time = 0, 0  # reset the elapsed time variables
        self.main_gui.data_text.delete("1.0", tk.END)
        self.main_gui.time_label.configure(text="{:.3f}s".format(elapsed_time))
        self.main_gui.state_time_label.configure(
            text="{:.3f}s".format(state_elapsed_time)
        )

    def stop_program(self) -> None:
        """Method to halt the program and set it to the off state, changing the button back to start."""
        self.state = "OFF"

        # set the state timer label
        self.main_gui.state_time_label_header.configure(text=(self.state))

        # set the running variable to false to halt execution in the state functions
        self.running = False

        # Turn the program execution button back to the green start button
        self.main_gui.startButton.configure(text="Start", bg="green")

        for after_id in (
            self.after_ids
        ):  # cancel all after calls which cancels every recursive function call
            self.main_gui.root.after_cancel(after_id)

        self.after_ids.clear()

        self.arduino_mgr.reset_arduinos()  # send the reset command to reboot both Arduino boards
        self.current_trial_number = 1

    def start_program(self) -> None:
        # Start the program if it is not already runnning and generate random numbers
        self.running = True

        # program main start time begins now
        self.data_mgr.start_time = time.time()
        self.data_mgr.state_start_time = time.time()

        self.update_clock_label()

        # turn the main button to the red stop button
        self.main_gui.startButton.configure(text="Stop", bg="red")

        # call the first ITI state with an iteration variable (i acts as a
        # variable to iterate throgh the program schedule data table) starting at 0
        self.initial_time_interval(0)

    def update_clock_label(self) -> None:
        # if the program is running, update the clock label
        if self.running:
            self.main_gui.update_clock_label()
