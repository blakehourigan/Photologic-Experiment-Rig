import logging
import datetime
from logging import FileHandler
from pathlib import Path

# Model (data) classe / sub-classes are init'd internally to this class
from models.experiment_process_data import ExperimentProcessData

# GUI classes
from views.main_gui import MainGUI

# controller classes
from controllers.arduino_control import ArduinoManager


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler for errors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)

# Rotating file handler for all logs, this means that once maxBytes is exceeded, the data rolls over into a new file.
# for example, data will begin in app.log, then will roll over into app1.log

logfile_dir = Path(__file__).parent.parent.resolve()
now = datetime.datetime.now()
logfile_name = f"{now.hour}_{now.minute}_{now.second} - {now.date()} experiment log"
logfile_path = logfile_dir / "logfiles" / f"{logfile_name}"


file_handler = FileHandler(logfile_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


class TkinterApp:
    def __init__(self) -> None:
        try:
            # init exp_data, which initializes event_data, stimuli_data, arduino_data
            self.exp_data = ExperimentProcessData()

            """
            init views (gui windows), passing the reference to the data it will need, along with the 'trigger' function,
            which is used to transition the program from one state to another. Trigger is needed to manipulate state via
            the start and reset buttons
            """
            self.arduino_controller = ArduinoManager(self.exp_data, self.process_queue)

            self.main_gui = MainGUI(
                self.exp_data, self.trigger, self.arduino_controller
            )

            logging.info("GUI started successfully.")
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            raise
