import time 
import tkinter as tk

# Helper classes
from arduino_control import AduinoManager
from experiment_config import Config
from data_management import DataManager

# GUI classses
from main_gui import MainGUI
from rasterized_data_window import RasterizedDataWindow
from experiment_control_window import ExperimentCtlWindow
from licks_window import LicksWindow
from valve_testing_window import ValveTestWindow
from valve_testing_logic import valveTestLogic
from program_schedule import ProgramScheduleWindow
from valve_control_window import ControlValves
from prime_valves import PrimeValves

class ProgramController:
    def __init__(self, restart_callback = None) -> None:
        self.restart_callback = restart_callback

        self.experiment_config = Config()

        self.main_gui = MainGUI(self)
        self.data_window = RasterizedDataWindow(self)
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
        if(iteration == 0):
            self.data_mgr.initalize_licks_dataframe()
        
        elif(iteration > 0):
            lick_stamps_side_one, lick_stamps_side_two = self.data_mgr.get_lick_timestamps(iteration)
            self.data_mgr.side_one_trial_licks.append(lick_stamps_side_one)
            self.data_mgr.side_two_trial_licks.append(lick_stamps_side_two)
            if self.data_window.side1_window is not None: 
                self.data_window.update_plot(self.data_window.side1_window, lick_stamps_side_one, iteration) 
            if self.data_window.side2_window is not None:
                self.data_window.update_plot(self.data_window.side2_window, lick_stamps_side_two, iteration) 
        """ If we have pressed start, and the current trial number is less than the number of trials determined by number of stim * number of trial blocks, 
            then continue running through more trials"""
            
        self.data_mgr.current_iteration = iteration
        
        if self.data_mgr.current_trial_number > (self.data_mgr.num_trials.get()):
            
            self.program_schedule_window.update_licks_and_TTC_actual(iteration + 1)
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
                self.data_mgr.stimuli_dataframe.loc[iteration, "Port 1"],
                self.data_mgr.stimuli_dataframe.loc[iteration, "Port 2"],
            )

            # add the initial interval to the program information box
            ITI_Value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "ITI")

            self.main_gui.update_on_state_change(ITI_Value, self.state)

            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            self.main_gui.root.after(int(ITI_Value), lambda: self.ITI_TTC_Transition(iteration))

    def ITI_TTC_Transition(self, iteration: int) -> None:
        door_close_time = 2238 # number of milliseconds until door close 
        
        self.send_command_to_arduino(arduino='motor', command="<D>") # tell motor arduino to move the door down
        
        self.main_gui.root.after(door_close_time, lambda: self.time_to_contact(iteration))
        self.data_mgr.state_start_time = time.time()  # state start time begins
        self.main_gui.clear_state_time()

    def time_to_contact(self, iteration: int):
        """defining the TTC state method, argument are self and iteration. iteration is passed from ITI to keep track of what stimuli we are on."""
        if self.running:
            """start reading licks, we pass the same i into this function that we used in the previous function to
            keep track of where we are storing the licks in the data table"""
            self.state = "TTC"
            
            self.main_gui.state_timer_text.configure(
                text=(self.state + " Time:")
            )  # update state timer header

            self.data_mgr.state_start_time = time.time()  # state start time begins

            """ Look in the dataframe in the current trial for the stimulus to give, once found mark the index with corresponding solenoid
            valve number and save into stimulus position variables. """


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
            self.send_command_to_arduino(arduino='laser', command="B") # Tell the laser arduino to begin accepting licks and opening valves

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

        self.queue_id = self.main_gui.root.after(100, self.process_queue)  # Reschedule after 100
              
    def parse_timestamps(self, timestamp_string):
        entries = timestamp_string.split('><')
        entries[0] = entries[0][1:]  # Remove the leading '<' from the first entry
        entries[-1] = entries[-1][:-1]  # Remove the trailing '>' from the last entry
        parsed_entries = []

        for entry in entries:
            parts = entry.split(',')
            command = parts[0]
            trial_number = int(parts[1])
            occurrence_time = int(parts[2])

            timestamp = {
                'command': command,
                'trial_number': trial_number,
                'occurrence_time': occurrence_time 
            }
            parsed_entries.append(timestamp)

        return parsed_entries

    def process_data(self, source, data):
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
                modified_data = data[1:-1]  # Remove the first and last characters
                self.send_lick_data_to_dataframe(modified_data)
            
            if (self.data_mgr.side_one_licks > 2 or self.data_mgr.side_two_licks > 2) and self.state == "TTC":
                self.start_new_sample(self.data_mgr.current_iteration)        

        elif source == 'motor':
            if data == "<Finished Pair>":
                # if the motor arduino has finished testing a pair of valves, then append the data we get from the volumes to the volumes lists
                self.valve_test_logic.append_to_volumes()
            elif "Durations" in data:
                self.valve_test_logic.begin_updating_opening_times(data)
            elif "SCHEDULE VERIFICATION" in data:
                cleaned_data = data.replace("SCHEDULE VERIFICATION", "").strip()
                print(cleaned_data)
                self.data_mgr.verify_arduino_schedule(self.data_mgr.side_one_indexes, self.data_mgr.side_two_indexes, cleaned_data)
            elif "Time Stamp Data" in data: 
                cleaned_data = data.replace("Time Stamp Data", "").strip()
                motor_timestamps = self.parse_timestamps(cleaned_data)
                self.data_mgr.insert_trial_start_stop_into_licks_dataframe(motor_timestamps)

    def send_lick_data_to_dataframe(self, stimulus):
        data_mgr = self.data_mgr
        licks_dataframe = data_mgr.licks_dataframe
        total_licks = data_mgr.total_licks

        if stimulus == "Stimulus One":
            stimulus = '1'
        else:
            stimulus = '2'

        licks_dataframe.loc[total_licks, "Trial Number"] = data_mgr.current_trial_number

        licks_dataframe.loc[total_licks, "Licked Port"] = (
            int(stimulus)  # Send which stimulus was licked on this lick
        )
        licks_dataframe.loc[total_licks, "Time Stamp"] = (
            round(time.time() - data_mgr.start_time, 3)
        )

        licks_dataframe.loc[total_licks, "State"] = self.state

    def start_new_sample(self, iteration):
        """define method for checking licks during the TTC state"""
        self.data_mgr.stimuli_dataframe.loc[self.data_mgr.current_trial_number - 1, "TTC Actual"] = (time.time() - self.data_mgr.state_start_time) * 1000

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
       # 1. Cancel all pending after() calls in Tkinter
        if self.main_gui and self.main_gui.root:
            for after_id in self.after_ids:
                self.main_gui.root.after_cancel(after_id)
            self.main_gui.root.after_cancel(self.queue_id)
            self.after_ids.clear()

        # 2. Close all GUI windows
        self.close_all_tkinter_windows()

        # 3. Disconnect Arduino connections
        if self.arduino_mgr:
            self.arduino_mgr.close_connections()

        # 4. Ensure all data is saved and finalized
        # if self.data_mgr:
        #     self.data_mgr.finalize_data()

        # 5. Reset any other state as necessary
        self.state = "OFF"
        self.running = False
        
        self.restart_callback()  # Call the restart function

    def close_all_tkinter_windows(self):
        # ensure any secondary windows are closed
        windows = [self.data_window, self.licks_window, self.experiment_ctl_wind, 
                self.program_schedule_window, self.valve_testing_window, 
                getattr(self, 'valve_control_window', None)]  # Use getattr for safe access
        for win in windows:
            if win and hasattr(win, 'top') and hasattr(win.top, 'winfo_exists') and win.top.winfo_exists():
                win.top.destroy()
        # Close the main window and any other open windows
        if hasattr(self, 'main_gui') and hasattr(self.main_gui, 'root') and self.main_gui.root:
            self.main_gui.root.destroy()  # This destroys the main window


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
            5000, self.complete_program
        )  # send the reset command to reboot both Arduino boards

        self.after_ids.clear()

        self.data_mgr.current_trial_number = 1

    def complete_program(self)-> None:
        # Request the timestamp data from the motor arduino
        self.send_command_to_arduino(arduino='motor', command="<9>")
        self.arduino_mgr.reset_arduinos()

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

            self.send_command_to_arduino(arduino='motor', command="<0>")

            self.main_gui.update_clock_label()

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
        # Check if the window is already open and if so, bring it to focus
        if hasattr(self, 'valve_control_window') and self.valve_control_window.top.winfo_exists():
            self.valve_control_window.top.lift()
        else:
            # Otherwise, create a new instance of the window
            self.valve_control_window = ControlValves(self)
        
    def open_rasterized_data_windows(self) -> None:
        if self.data_mgr.blocks_generated:
            self.data_window.show_window(1)
            self.data_window.show_window(2)
        else: 
            print('blocks not yet generated')


    def send_command_to_arduino(self, arduino, command) -> None:
        if arduino == 'laser':
            self.arduino_mgr.send_command_to_laser(command)
        elif arduino == 'motor':
            self.arduino_mgr.send_command_to_motor(command)
        
    def get_total_number_valves(self) -> int:
        return self.experiment_config.maximum_num_valves
    
    def get_window_icon_path(self)-> str:
        return self.experiment_config.get_window_icon_path()
        
    def show_stimuli_table(self) -> None:
        self.program_schedule_window.show_stimuli_table()
    
    def show_valve_stimuli_window(self) -> None:
        self.experiment_ctl_wind.show_window(self.main_gui.root)
        
    def launch_prime_valves_window(self) -> None:
        self.prime_valves_window = PrimeValves(self)

    def run_valve_test(self, num_valves_to_test) -> None:
        self.valves_to_test = num_valves_to_test
        self.valve_test_logic.start_valve_test_sequence(num_valves_to_test)
        
    def display_gui_error(self, error, message) -> None:
        self.main_gui.display_error(error=error, message=message)
        
    def get_num_trials(self) -> int:
        return self.data_mgr.num_trials
    
    def get_num_stimuli(self) -> int:
        return self.data_mgr.num_stimuli
    
    def get_current_trial(self) -> int:
        return self.data_mgr.current_trial_number
    
    def get_num_trial_blocks_variable_reference(self) -> tk.IntVar:
        return self.data_mgr.get_num_trial_blocks_var()
    
    # this function passes the num_stimuli variable directly from the data manager class to the gui class without jumping through many classes in the gui class itself
    def get_num_stimuli_variable_reference(self) -> tk.IntVar:
        return self.data_mgr.get_num_stimuli_var_reference()