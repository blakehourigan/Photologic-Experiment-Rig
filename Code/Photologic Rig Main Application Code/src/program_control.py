import time 
import re 

# Helper classes
from arduino_control import AduinoManager
from experiment_config import Config
from data_management import DataManager

# GUI classses
from main_gui import MainGUI
from data_window import DataWindow
from experiment_control_window import ExperimentCtlWindow
from licks_window import LicksWindow
from test_valves_window import ValveTestWindow
from test_valves_logic import valveTestLogic
from program_schedule import ProgramScheduleWindow
from valve_control import ValveControl


class ProgramController:
    def __init__(self) -> None:
        self.config = Config()

        self.main_gui = MainGUI(self)
        self.data_window = DataWindow(self)
        self.licks_window = LicksWindow(self)
        self.experiment_ctl_wind = ExperimentCtlWindow(self)
        self.program_schedule_window = ProgramScheduleWindow(self)

        self.data_mgr = DataManager(self)
        self.arduino_mgr = AduinoManager(self)

        self.valve_testing_window = ValveTestWindow(self)
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

        if self.data_mgr.current_trial_number > (self.data_mgr.num_trials.get()):
            self.stop_program()  # if we have gone through every trial then end the program.

        elif self.running:
            self.state = "ITI"

            # new trial so reset the lick counters
            self.data_mgr.side_one_licks = 0
            self.data_mgr.side_two_licks = 0

            # configure the state time label in the top right of the main window to hold the value of the new state
            self.main_gui.state_timer_text.configure(text=(self.state + " Time:"))

            # update the state start time to now, so that it starts at 0
            self.data_mgr.state_start_time = time.time()

            self.main_gui.update_on_new_trial(
                self.data_mgr.stimuli_dataframe.loc[iteration, "Side 1"],
                self.data_mgr.stimuli_dataframe.loc[iteration, "Side 2"],
            )

            # add the initial interval to the program information box
            ITI_Value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "ITI")

            self.main_gui.update_on_state_change(ITI_Value, self.state)

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

            
            self.check_licks_above_TTC_threshold(
                iteration
            )  # check if we have 3 licks from either side
            
            self.main_gui.state_timer_text.configure(
                text=(self.state + " Time:")
            )  # update state timer header

            self.data_mgr.state_start_time = time.time()  # state start time begins

            command = "<D>"  # tell motor arduino to move the door down
            self.arduino_mgr.send_command_to_motor(command)

            """ Look in the dataframe in the current trial for the stimulus to give, once found mark the index with corresponding solenoid
            valve number and save into stimulus position variables. """

            (
                stimulus_1_position,
                stimulus_2_position,
            ) = self.data_mgr.find_stimuli_positions(iteration)

            TTC_Value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "TTC")

            self.main_gui.update_on_state_change(TTC_Value, self.state)

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
            command = "B"
            self.arduino_mgr.send_command_to_laser(command)

            # Update the state start time to the current time
            self.data_mgr.state_start_time = time.time()

            sample_interval_value = self.data_mgr.check_dataframe_entry_isfloat(
                iteration, "Sample Time"
            )

            self.main_gui.update_on_state_change(sample_interval_value, self.state)

            # After the sample time specified in the ith row of the 'Sample Time' table, we will jump to the save licks function
            self.main_gui.root.after(
                int(sample_interval_value), lambda: self.data_mgr.save_licks(iteration)
            )

    def process_queue(self):
        while not self.arduino_mgr.data_queue.empty():
            source, data = self.arduino_mgr.data_queue.get()
            self.process_data(source, data)
        self.main_gui.root.after(100, self.process_queue)  # Reschedule after 100 ms  
              
    def process_data(self, source, data):
        duration_pattern = r"<S1, (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), S2, (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+)>"
        # Process the data from the queue
        if source == 'laser':
            # Handle laser data
            if (data == "<Stimulus One>" or data == "<Stimulus Two>") and ((self.state == "TTC") or (self.state == "Sample")):
                if (data == "<Stimulus One>"):
                    self.data_mgr.side_one_licks += 1
                    self.data_mgr.total_licks += 1
                elif data == "<Stimulus Two>":
                    self.data_mgr.side_two_licks += 1
                    self.data_mgr.total_licks += 1
            
            self.check_licks_above_TTC_threshold()
                        
            modified_data = data[1:-1]  # Remove the first and last characters
            self.send_lick_data_to_dataframe(modified_data)
        elif source == 'motor':
            match = re.search(duration_pattern, data)
            if data == "<Finished Pair>":
                self.valve_test_logic.append_to_volumes()
            elif match:
                self.valve_test_logic.begin_updating_opening_times(data)
            elif "SCHEDULE VERIFICATION" in data:
                cleaned_data = data.replace("SCHEDULE VERIFICATION", "").strip()
                self.arduino_mgr.verify_schedule(self.arduino_mgr.side_one_indexes, self.arduino_mgr.side_two_indexes, cleaned_data)

    def send_lick_data_to_dataframe(self, stimulus):
        data_mgr = self.data_mgr
        licks_dataframe = data_mgr.licks_dataframe
        total_licks = data_mgr.total_licks

        licks_dataframe.loc[total_licks, "Trial Number"] = data_mgr.current_trial_number

        licks_dataframe.loc[total_licks, "Port Licked"] = (
            stimulus  # Send which stimulus was licked on this lick
        )
        licks_dataframe.loc[total_licks, "Time Stamp"] = (
            time.time() - data_mgr.start_time
        )

        licks_dataframe.loc[total_licks, "State"] = self.state

    def check_licks_above_TTC_threshold(self, iteration):
        """define method for checking licks during the TTC state"""
        self.TTC_lick_threshold = self.data_mgr.TTC_lick_threshold

        if (
            self.data_mgr.side_one_licks >= self.data_mgr.TTC_lick_threshold.get()
            or self.data_mgr.side_two_licks >= self.data_mgr.TTC_lick_threshold.get()
        ) and self.state == "TTC":
            self.data_mgr.stimuli_dataframe.loc[
                self.data_mgr.current_trial_number - 1, "TTC Actual"
            ] = (time.time() - self.data_mgr.state_start_time) * 1000

            self.main_gui.root.after_cancel(self.after_sample_id)
            self.data_mgr.side_one_licks = 0
            self.data_mgr.side_two_licks = 0
            self.sample_time(iteration)


    def start_button_handler(self) -> None:
        """Handle toggling the program to running/not running on click of the start/stop button"""
        if self.running:
            self.stop_program()
        else:
            self.start_program()

    def reset_button_handler(self) -> None:
        """Handle clearing the data window on click of the clear button"""
        self.main_gui.update_on_reset()
        self.experiment_ctl_wind.reset_traces()
        if (
            self.experiment_ctl_wind.top is not None
            and self.experiment_ctl_wind.top.winfo_exists()
        ):
            self.experiment_ctl_wind.on_window_close()
            self.experiment_ctl_wind.show_window(self.main_gui.root)
        self.data_mgr.reset_all()
        self.arduino_mgr.close_connections()

        self.arduino_mgr = AduinoManager(self)

    def stop_program(self) -> None:
        """Method to halt the program and set it to the off state, changing the button back to start."""
        self.state = "OFF"

        # set the running variable to false to halt execution in the state functions
        self.running = False

        self.main_gui.update_on_stop()

        for after_id in (
            self.after_ids
        ):  # cancel all after calls which cancels every recursive function call
            self.main_gui.root.after_cancel(after_id)

        self.main_gui.root.after(
            5000, self.arduino_mgr.reset_arduinos
        )  # send the reset command to reboot both Arduino boards

        self.after_ids.clear()

        self.data_mgr.current_trial_number = 1

    def start_program(self) -> None:
        # Start the program if it is not already runnning and generate random numbers

        if not self.data_mgr.blocks_generated:
            self.main_gui.display_error(
                "Blocks not Generated",
                "Please generate blocks before starting the program.",
            )
            self.experiment_ctl_wind.show_window(self.main_gui.root)
        else:
            self.running = True

            # program main start time begins now
            self.data_mgr.start_time = time.time()
            self.data_mgr.state_start_time = time.time()

            self.update_clock_label()

            # turn the main button to the red stop button
            self.main_gui.start_button.configure(text="Stop", bg="red")

            # call the first ITI state with an iteration variable (i acts as a
            # variable to iterate throgh the program schedule data table) starting at 0
            self.initial_time_interval(0)

    def update_clock_label(self) -> None:
        # if the program is running, update the clock label
        if self.running:
            self.main_gui.update_clock_label()

    def open_valve_control_window(self):
        # Assuming ValveControl is imported at the top of this file
        self.valve_control_window = ValveControl(self)
