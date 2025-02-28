import logging
from logging.handlers import RotatingFileHandler

# Model (data) classe / sub-classes are init'd internally to this class
from models.experiment_process_data import ExperimentProcessData

# GUI classes
from views.main_gui import MainGUI

# controller classes
from controllers.arduino_control import ArduinoManager


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Console handler for errors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)

# Rotating file handler for all logs, this means that once maxBytes is exceeded, the data rolls over into a new file.
# for example, data will begin in app.log, then will roll over into app1.log
file_handler = RotatingFileHandler("app.log", maxBytes=10 * 1024 * 1024, backupCount=3)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


class TkinterApp:
    def __init__(self) -> None:
        try:
            # init exp_data, which initializes licks_data, stimuli_data, arduino_data
            self.init_models()

            # self.init_controllers()
            # self.arduino_controller.send_arduino_json_data()

            """
            init views (gui windows), passing the reference to the data it will need, along with the 'trigger' function,
            which is used to transition the program from one state to another. Trigger is needed to manipulate state via
            the start and reset buttons
            """
            self.init_view(self.exp_data, self.trigger)
            logging.info("GUI started successfully.")
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            raise

    def init_models(self):
        self.exp_data = ExperimentProcessData()

        logging.info("Data Classes initialized.")

    def init_controllers(self):
        """Initialize managers."""
        self.arduino_controller = ArduinoManager(self)

        logging.info("Controllers initialized.")

    def init_view(self, exp_data, trigger):
        # instantiating MainGUI sets up our gui and the objects needed
        self.main_gui = MainGUI(exp_data, trigger)

        logging.info("View (GUI) initialized.")
