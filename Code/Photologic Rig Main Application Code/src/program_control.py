import time
import tkinter as tk
import logging
from logging.handlers import RotatingFileHandler
import json

# Helper classes
from arduino_control import ArduinoManager
from experiment_config import Config
from data_management import DataManager

# GUI classes
from main_gui import MainGUI
from rasterized_data_window import RasterizedDataWindow
from experiment_control_window import ExperimentCtlWindow
from licks_window import LicksWindow
from valve_testing_window import ValveTestWindow
from valve_testing_logic import valveTestLogic
from program_schedule import ProgramScheduleWindow
from valve_control_window import ControlValves

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Console handler for errors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Rotating file handler for all logs
file_handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=3)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class ProgramController:
    def __init__(self, restart_callback=None) -> None:
        self.restart_callback = restart_callback
        self.running = False
        self.experiment_completed = False
        self.state = "OFF"
        self.after_ids: list[str] = []

        try:
            self.init_config()
            self.init_windows()
            self.init_managers()
            self.arduino_mgr.connect_to_arduino()
            self.init_logic()

            time.sleep(2)
            self.send_arduino_json_data()

            logging.info("ProgramController initialized successfully.")
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            raise

    def init_config(self):
        """Initialize configuration."""
        self.experiment_config = Config()
        logging.debug("Config initialized.")

    def init_managers(self):
        """Initialize managers."""
        self.data_mgr = DataManager(self)
        self.arduino_mgr = ArduinoManager(self)

        logging.debug("Managers initialized.")

    def init_windows(self):
        """Initialize GUI windows."""
        self.main_gui = MainGUI(self)
        self.data_window = RasterizedDataWindow(self)
        self.licks_window = LicksWindow(self)
        self.experiment_ctl_wind = ExperimentCtlWindow(self)
        self.program_schedule_window = ProgramScheduleWindow(self)
        self.valve_testing_window = ValveTestWindow(self)
        logging.debug("GUI windows initialized.")

    def init_logic(self):
        """Initialize logic components."""
        self.valve_test_logic = valveTestLogic(self)
        logging.debug("Logic components initialized.")

    def start_main_gui(self) -> None:
        """Start the main GUI and connect to the Arduino."""
        try:
            self.main_gui.setup_gui()

            logging.info("Arduino connected.")
            self.main_gui.root.mainloop()
            logging.info("Main GUI started.")
        except Exception as e:
            logging.error(f"Error starting main GUI: {e}")
            raise

    def initial_time_interval(self, iteration: int) -> None:
        """Handle the initial time interval state of the experiment."""
        if logger.isEnabledFor(logging.DEBUG):
            logging.debug(f"Initial time interval started for iteration {iteration}.")
        try:
            if iteration > 0:
                lick_stamps_side_one, lick_stamps_side_two = self.data_mgr.get_lick_timestamps(iteration)
                self.data_mgr.side_one_trial_licks.append(lick_stamps_side_one)
                self.data_mgr.side_two_trial_licks.append(lick_stamps_side_two)
                if self.data_window.side1_window is not None:
                    self.data_window.update_plot(self.data_window.side1_window, lick_stamps_side_one, iteration)
                if self.data_window.side2_window is not None:
                    self.data_window.update_plot(self.data_window.side2_window, lick_stamps_side_two, iteration)
            
            self.data_mgr.current_iteration = iteration
            
            if self.data_mgr.current_trial_number > self.get_num_trials():
                self.experiment_completed = True
                self.program_schedule_window.update_licks_and_TTC_actual(iteration + 1)
                self.stop_program()
            elif self.running:
                self.state = "ITI"
                self.data_mgr.side_one_licks = 0
                self.data_mgr.side_two_licks = 0
                self.main_gui.state_timer_text.configure(text=(self.state + " Time:"))
                self.data_mgr.state_start_time = time.time()
                self.main_gui.update_on_new_trial(
                    self.data_mgr.stimuli_dataframe.loc[iteration, "Port 1"],
                    self.data_mgr.stimuli_dataframe.loc[iteration, "Port 2"]
                )
                ITI_Value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "ITI")
                self.main_gui.update_on_state_change(ITI_Value, self.state)
                self.main_gui.root.after(int(ITI_Value), lambda: self.ITI_TTC_Transition(iteration))
            logging.debug(f"Initial time interval completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in initial time interval: {e}")
            raise

    def ITI_TTC_Transition(self, iteration: int) -> None:
        logging.debug(f"ITI to TTC transition started for iteration {iteration}.")
        try:
            door_close_time = 2238  # number of milliseconds until door close 
            self.send_command_to_arduino(arduino='motor', command="<D>")  # tell motor arduino to move the door down
            self.main_gui.root.after(door_close_time, lambda: self.time_to_contact(iteration))
            self.data_mgr.state_start_time = time.time()  # state start time begins
            self.main_gui.clear_state_time()
            logging.debug(f"ITI to TTC transition completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in ITI to TTC transition: {e}")
            raise

    def time_to_contact(self, iteration: int):
        """Handle the time to contact state."""
        logging.debug(f"Time to contact started for iteration {iteration}.")
        try:
            if self.running:
                self.state = "TTC"
                self.main_gui.state_timer_text.configure(text=(self.state + " Time:"))
                self.data_mgr.state_start_time = time.time()
                TTC_Value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "TTC")
                self.main_gui.update_on_state_change(TTC_Value, self.state)
                self.after_sample_id = self.main_gui.root.after(
                    int(TTC_Value), lambda: self.data_mgr.save_licks(iteration)
                )
                self.after_ids.append(self.after_sample_id)
            logging.debug(f"Time to contact completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in time to contact: {e}")
            raise

    def sample_time(self, iteration: int):
        """Handle the sample time state."""
        logging.debug(f"Sample time started for iteration {iteration}.")
        try:
            if self.running:
                self.state = "Sample"
                self.send_command_to_arduino(arduino='laser', command="B")  # Tell the laser arduino to begin accepting licks and opening valves
                self.data_mgr.state_start_time = time.time()
                sample_interval_value = self.data_mgr.check_dataframe_entry_isfloat(iteration, "Sample Time")
                self.main_gui.update_on_state_change(sample_interval_value, self.state)
                self.main_gui.root.after(
                    int(sample_interval_value), lambda: self.data_mgr.save_licks(iteration)
                )
            logging.debug(f"Sample time completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in sample time: {e}")
            raise

    def process_queue(self):
        """Process the data queue."""
        #logging.debug("Processing data queue.")
        try:
            while not self.arduino_mgr.data_queue.empty():
                source, data = self.arduino_mgr.data_queue.get()
                self.process_data(source, data)
            self.queue_id = self.main_gui.root.after(100, self.process_queue)  # Reschedule after 100
        except Exception as e:
            logging.error(f"Error processing data queue: {e}")
            raise

    def parse_timestamps(self, timestamp_string):
        """Parse timestamps from the Arduino data."""
        logging.debug(f"Parsing timestamps: {timestamp_string}")
        try:
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
            logging.debug(f"Timestamps parsed: {parsed_entries}")
            return parsed_entries
        except Exception as e:
            logging.error(f"Error parsing timestamps: {e}")
            raise

    def process_data(self, source, data):
        """Process data received from the Arduino."""
        logging.debug(f"Processing data from {source}: {data}")
        try:
            if source == 'laser':
                if (data == "<Stimulus One>" or data == "<Stimulus Two>") and (self.state in ["TTC", "Sample"]):
                    if data == "<Stimulus One>":
                        self.data_mgr.side_one_licks += 1
                        self.data_mgr.total_licks += 1
                    elif data == "<Stimulus Two>":
                        self.data_mgr.side_two_licks += 1
                        self.data_mgr.total_licks += 1
                    modified_data = data[1:-1]  # Remove the first and last characters
                    self.record_lick_data(modified_data)
                if (self.data_mgr.side_one_licks > 2 or self.data_mgr.side_two_licks > 2) and self.state == "TTC":
                    self.start_new_sample(self.data_mgr.current_iteration)        
            elif source == 'motor':
                if data == "<Finished Pair>":
                    self.valve_test_logic.append_to_volumes()
                elif "Testing Complete" in data:
                    self.valve_test_logic.begin_updating_opening_times(data)
                elif "SCHEDULE VERIFICATION" in data:
                    cleaned_data = data.replace("SCHEDULE VERIFICATION", "").strip()
                    self.data_mgr.verify_arduino_schedule(self.data_mgr.side_one_indexes, self.data_mgr.side_two_indexes, cleaned_data)
                elif "Time Stamp Data" in data:
                    cleaned_data = data.replace("Time Stamp Data", "").strip()
                    motor_timestamps = self.parse_timestamps(cleaned_data)
                    self.data_mgr.insert_trial_start_stop_into_licks_dataframe(motor_timestamps)
            logging.debug(f"Data processed from {source}: {data}")
        except Exception as e:
            logging.error(f"Error processing data from {source}: {e}")
            raise

    def record_lick_data(self, stimulus):
        """Record lick data to the dataframe."""
        logging.debug(f"Recording lick data: {stimulus}")
        try:
            data_mgr = self.data_mgr
            licks_dataframe = data_mgr.licks_dataframe
            total_licks = data_mgr.total_licks
            stimulus = '1' if stimulus == "Stimulus One" else '2'
            licks_dataframe.loc[total_licks, "Trial Number"] = data_mgr.current_trial_number
            licks_dataframe.loc[total_licks, "Licked Port"] = int(stimulus)
            licks_dataframe.loc[total_licks, "Time Stamp"] = round(time.time() - data_mgr.start_time, 3)
            licks_dataframe.loc[total_licks, "State"] = self.state
            logging.debug(f"Lick data recorded: {stimulus}")
        except Exception as e:
            logging.error(f"Error recording lick data: {e}")
            raise

    def start_new_sample(self, iteration):
        """Start a new sample after checking licks during the TTC state."""
        logging.debug(f"Starting new sample for iteration {iteration}.")
        try:
            self.data_mgr.stimuli_dataframe.loc[self.data_mgr.current_trial_number - 1, "TTC Actual"] = (time.time() - self.data_mgr.state_start_time) * 1000
            self.main_gui.root.after_cancel(self.after_sample_id)
            self.data_mgr.side_one_licks = 0
            self.data_mgr.side_two_licks = 0
            self.sample_time(iteration)
            logging.debug(f"New sample started for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error starting new sample: {e}")
            raise

    def start_button_handler(self) -> None:
        """Handle toggling the program to running/not running on click of the start/stop button."""
        logging.debug("Start button clicked.")
        try:
            if self.running:
                self.stop_program()
            else:
                self.start_program()
            logging.debug(f"Start button handler completed. Running: {self.running}")
        except Exception as e:
            logging.error(f"Error in start button handler: {e}")
            raise

    def reset_button_handler(self) -> None:
        """Handle resetting the program on click of the reset button."""
        logging.debug("Reset button clicked.")
        try:
            if self.main_gui and self.main_gui.root:
                for after_id in self.after_ids:
                    self.main_gui.root.after_cancel(after_id)
                self.main_gui.root.after_cancel(self.queue_id)
                self.after_ids.clear()
            self.close_all_tkinter_windows()
            if self.arduino_mgr:
                self.arduino_mgr.close_connections()
            self.state = "OFF"
            self.running = False
            self.restart_callback()
            logging.debug("Reset button handler completed.")
        except Exception as e:
            logging.error(f"Error in reset button handler: {e}")
            raise

    def close_all_tkinter_windows(self):
        """Close all secondary Tkinter windows."""
        logging.debug("Closing all Tkinter windows.")
        try:
            windows = [self.data_window, self.licks_window, self.experiment_ctl_wind, 
                       self.program_schedule_window, self.valve_testing_window, 
                       getattr(self, 'valve_control_window', None)]
            for win in windows:
                if win and hasattr(win, 'top') and hasattr(win.top, 'winfo_exists') and win.top.winfo_exists():
                    win.top.destroy()
            if hasattr(self, 'main_gui') and hasattr(self.main_gui, 'root') and self.main_gui.root:
                self.main_gui.root.destroy()
            logging.debug("All Tkinter windows closed.")
        except Exception as e:
            logging.error(f"Error closing Tkinter windows: {e}")
            raise

    def stop_program(self) -> None:
        """Method to halt the program and set it to the off state."""
        logging.debug("Stopping program.")
        try:
            self.state = "OFF"
            self.running = False
            self.main_gui.update_on_stop()
            for after_id in self.after_ids:
                self.main_gui.root.after_cancel(after_id)
            self.main_gui.root.after(5000, self.complete_program)
            self.after_ids.clear()
            self.data_mgr.current_trial_number = 1
            logging.debug("Program stopped.")
        except Exception as e:
            logging.error(f"Error stopping program: {e}")
            raise

    def complete_program(self) -> None:
        """Complete the program and reset Arduinos."""
        logging.debug("Completing program.")
        try:
            self.send_command_to_arduino(arduino='motor', command="<9>")
            self.arduino_mgr.reset_arduinos()
            if self.experiment_completed:
                self.data_mgr.save_data_to_xlsx()
            logging.debug("Program completed and Arduinos reset.")
        except Exception as e:
            logging.error(f"Error completing program: {e}")
            raise

    def start_program(self) -> None:
        """Start the program if it is not already running."""
        logging.debug("Starting program.")
        try:
            if not self.data_mgr.blocks_generated:
                self.main_gui.display_error(
                    "Blocks not Generated",
                    "Please generate blocks before starting the program.",
                )
                self.experiment_ctl_wind.show_window(self.main_gui.root)
            else:
                self.running = True
                self.data_mgr.start_time = time.time()
                self.data_mgr.state_start_time = time.time()
                self.send_command_to_arduino(arduino='motor', command="<0>")
                self.main_gui.update_clock_label()
                self.main_gui.start_button.configure(text="Stop", bg="red")
                self.initial_time_interval(0)
                logging.debug("Program started.")
        except Exception as e:
            logging.error(f"Error starting program: {e}")
            raise

    def update_clock_label(self) -> None:
        """Update the clock label if the program is running."""
        logging.debug("Updating clock label.")
        try:
            if self.running:
                self.main_gui.update_clock_label()
            logging.debug("Clock label updated.")
        except Exception as e:
            logging.error(f"Error updating clock label: {e}")
            raise

    def open_valve_control_window(self):
        """Open or focus the valve control window."""
        logging.debug("Opening valve control window.")
        try:
            if hasattr(self, 'valve_control_window') and self.valve_control_window.top.winfo_exists():
                self.valve_control_window.top.lift()
            else:
                self.valve_control_window = ControlValves(self)
            logging.debug("Valve control window opened.")
        except Exception as e:
            logging.error(f"Error opening valve control window: {e}")
            raise

    def open_rasterized_data_windows(self) -> None:
        """Open the rasterized data windows if blocks are generated."""
        logging.debug("Opening rasterized data windows.")
        try:
            if self.data_mgr.blocks_generated:
                self.data_window.show_window(1)
                self.data_window.show_window(2)
            else:
                self.display_gui_error(
                    "Blocks Not Generated",
                    "Experiment blocks haven't been generated yet, please generate trial blocks and try again",
                )
                logging.warning("Blocks not yet generated.")
            logging.debug("Rasterized data windows opened.")
        except Exception as e:
            logging.error(f"Error opening rasterized data windows: {e}")
            raise

    def send_command_to_arduino(self, arduino, command) -> None:
        """Send a command to the specified Arduino."""
        try:
            if arduino == 'laser':
                self.arduino_mgr.send_command_to_laser(command)
            elif arduino == 'motor':
                self.arduino_mgr.send_command_to_motor(command)
        except Exception as e:
            logging.error(f"Error sending command to {arduino} Arduino: {e}")
            raise

    def get_total_number_valves(self) -> int:
        """Get the total number of valves from the configuration."""
        return self.experiment_config.maximum_num_valves
    
    def get_window_icon_path(self) -> str:
        """Get the window icon path from the configuration."""
        return self.experiment_config.get_window_icon_path()
        
    def show_stimuli_table(self) -> None:
        """Show the stimuli table."""
        logging.debug("Showing stimuli table.")
        try:
            self.program_schedule_window.show_stimuli_table()
            logging.debug("Stimuli table shown.")
        except Exception as e:
            logging.error(f"Error showing stimuli table: {e}")
            raise
    
    def show_valve_stimuli_window(self) -> None:
        """Show the valve stimuli window."""
        logging.debug("Showing valve stimuli window.")
        try:
            self.experiment_ctl_wind.show_window(self.main_gui.root)
            logging.debug("Valve stimuli window shown.")
        except Exception as e:
            logging.error(f"Error showing valve stimuli window: {e}")
            raise
    
    def run_valve_test(self, num_valves_to_test) -> None:
        """Run the valve test for the specified number of valves."""
        logging.debug(f"Running valve test for {num_valves_to_test} valves.")
        try:
            self.valves_to_test = num_valves_to_test
            self.valve_test_logic.start_valve_test_sequence(num_valves_to_test)
            logging.debug(f"Valve test started for {num_valves_to_test} valves.")
        except Exception as e:
            logging.error(f"Error running valve test for {num_valves_to_test} valves: {e}")
            raise
        
    def display_gui_error(self, error, message) -> None:
        """Display an error message in the GUI."""
        logging.error(f"Displaying GUI error: {error} - {message}")
        try:
            self.main_gui.display_error(error=error, message=message)
            logging.debug("GUI error displayed.")
        except Exception as e:
            logging.error(f"Error displaying GUI error: {e}")
            raise
        
    def get_num_trials(self) -> int:
        """Get the number of trials."""
        return self.data_mgr.num_trials
    
    def get_num_stimuli(self) -> int:
        """Get the number of stimuli."""
        return self.data_mgr.num_stimuli
    
    def get_current_trial(self) -> int:
        """Get the current trial number."""
        return self.data_mgr.current_trial_number
    
    def get_num_trial_blocks_variable_reference(self) -> tk.IntVar:
        """Get the number of trial blocks as a Tkinter variable reference."""
        return self.data_mgr.get_num_trial_blocks_var()
    
    def get_num_stimuli_variable_reference(self) -> tk.IntVar:
        """Get the number of stimuli as a Tkinter variable reference."""
        return self.data_mgr.get_num_stimuli_var_reference()
    
    def close_valve_stimuli_window(self) -> None:
        """Close the valve stimuli window."""
        logging.debug("Closing valve stimuli window.")
        try:
            self.experiment_ctl_wind.close_window()
            logging.debug("Valve stimuli window closed.")
        except Exception as e:
            logging.error(f"Error closing valve stimuli window: {e}")
            raise
        
    def generate_experiment_schedule(self) -> None:
        """Generate the experiment schedule."""
        logging.debug("Generating experiment schedule.")
        try:
            self.data_mgr.initialize_stimuli_dataframe()
            self.data_mgr.initalize_licks_dataframe()
            self.close_valve_stimuli_window()
            self.program_schedule_window.show_stimuli_table()
            logging.debug("Experiment schedule generated.")
        except Exception as e:
            logging.error(f"Error generating experiment schedule: {e}")
            raise

    def get_current_json_config(self) -> dict:
        return self.data_mgr.load_configuration(config_name="last_used")

    def save_current_json_config(self, arduino_data) -> None:
        self.data_mgr.save_configuration(config_data=arduino_data)

    def send_arduino_json_data(self):
        arduino_data = self.get_current_json_config()
        
        # Convert the dictionary to a JSON string
        json_data = json.dumps(arduino_data)
        
        arduino_command = '<A,' + json_data + '>'
        
        print(arduino_command)
        
        self.send_command_to_arduino(arduino='motor', command=arduino_command)

# Main function
def main():
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        controller = ProgramController()
        controller.start_main_gui()
    except Exception as e:
        logging.critical(f"Critical error in main: {e}")

if __name__ == "__main__":
    main()
