"""
This module defines the ExperimentCtlWindow class, a Toplevel window in the GUI responsible
for allowing the user to assign specific substances (stimuli) to the different valves available
on the experimental rig.

It generates labels and input fields for these stimuli based on the number of stimuli
defined in the experiment variables and ensures symmetrical assignment between corresponding valves
on opposing sides. This ensures that each simulus used is used on both sides. It also includes the button to trigger the
generation of the experiment schedule after stimuli assignments are complete.
"""

import tkinter as tk
import logging
from tkinter import ttk
from typing import Callable, Dict, List

from models.experiment_process_data import ExperimentProcessData
from models.stimuli_data import StimuliData
from views.gui_common import GUIUtils

# Get the logger in use to log info here
logger = logging.getLogger()


class ExperimentCtlWindow(tk.Toplevel):
    """
    This class defines a Toplevel window for managing experiment stimuli assignments to specific valves.
    It allows users to input the substance associated with each valve, ensures symmetry between
    corresponding valves on Side One and Side Two (e.g., Valve 1 mirrors Valve 5), and provides a button
    to trigger the generation of the experiment schedule based on these assignments and other experiment variables.

    Attributes
    ----------
    - **exp_process_data** (*ExperimentProcessData*): Reference to the main `models.exp_process_data` model, used to access
      variables like 'Num Stimuli' and trigger schedule generation.
    - **stimuli_data** (*StimuliData*): Reference to the model holding stimuli/valve assignment data. Used to
      get default values and update the model when user input changes.
    - **trigger** (*Callable[[str], None]*): A callback function from StateMachine class.
      that is called when the 'Generate Schedule' button is pressed to transition the application state to `GENERATE SCHEDULE` state.
    - **stimuli_entries** (*Dict[str, tk.StringVar]*): A dictionary mapping valve identifier strings (e.g., "Valve 1 Substance")
      to `tk.StringVar` objects. These variables are linked to the corresponding Entry widgets.
    - **stimuli_frame** (*ttk.Frame*): The main container frame within the Toplevel window.
    - **stimuli_entry_frame** (*tk.Frame*): A frame nested within `stimuli_frame`, specifically holding the
      labeled entry widgets for valve substance input, organized into two columns.
    - **ui_components** (*Dict[str, List[tk.Widget]]*): A dictionary storing lists of created UI widgets
      (frames, labels, entries) within `populate_stimuli_frame`. This allows for potential future access or modification.

    Methods
    -------
    - `show()`
        Makes the window visible (`deiconify`). It also checks if the 'Num Stimuli' variable in `exp_process_data` has
        changed since the UI was last built; if so, it re-initializes the content using `init_content()`.
    - `generate_button_method()`
        Callback for the 'Generate Schedule' button. It first triggers the schedule generation logic within the
        `exp_process_data` model. If successful, it hides the current window (`withdraw`) and calls the `trigger`
        function with the "GENERATE SCHEDULE" state/event.
    - `init_content()`
        Builds or rebuilds the main content of the window, including the `stimuli_frame`, populating it with valve
        entries using `populate_stimuli_frame`, and creating the 'Generate Schedule' button.
    - `fill_reverse_stimuli(source_var: tk.StringVar, mapped_var: tk.StringVar)`
        A callback function attached via `trace_add` to the `tk.StringVar`s in `stimuli_entries`. When the text in
        a valve's entry widget (linked to `source_var`) changes, this function automatically updates the `tk.StringVar`
        (`mapped_var`) of the corresponding valve on the opposite side (e.g., changing Valve 1 updates Valve 5's variable).
    - `populate_stimuli_frame()`
        Areates and arranges the `tk.Label` and `tk.Entry` widgets for each relevant valve within the
        `stimuli_entry_frame`. It organizes them into "Side One" and "Side Two" columns based on the 'Num Stimuli'
        variable. It also sets up the `trace_add` callbacks using `fill_reverse_stimuli` to link corresponding valves.
        Stores created widgets in `self.ui_components`.
    """

    def __init__(
        self,
        exp_data: ExperimentProcessData,
        stimuli_data: StimuliData,
        trigger: Callable[[str], None],
    ):
        """
        Initialize the ExperimentCtlWindow. Sets up data model references, the trigger callback,
        window attributes (title, close protocol, bindings), Tkinter variables for stimuli,
        links variables to the model, initializes UI content, and hides the window.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): Instance holding experiment variables and methods.
        - **stimuli_data** (*StimuliData*): Instance holding stimuli assignment data and logic.
        - **trigger** (*Callable[[str], None]*): Callback function to signal state transitions (e.g., "GENERATE SCHEDULE").
        """
        super().__init__()
        self.exp_process_data = exp_data
        self.stimuli_data = stimuli_data

        # a callback function to immediately show the program window upon genration of schec
        self.trigger = trigger

        # init window attributes
        self.title("Stimuli / Valves")
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        # lambda requires event here, because it captures the keypress event in case you wanna pass that to the fucntion,
        # but we don't so we do not use it. still, it is required to capture it
        self.bind("<Control-w>", lambda event: self.withdraw())
        self.resizable(False, False)

        # set grid row and col zero to expand to fill the available space
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # tkinter variables for stimuli variables
        self.stimuli_entries = {
            "Valve 1 Substance": tk.StringVar(),
            "Valve 2 Substance": tk.StringVar(),
            "Valve 3 Substance": tk.StringVar(),
            "Valve 4 Substance": tk.StringVar(),
            "Valve 5 Substance": tk.StringVar(),
            "Valve 6 Substance": tk.StringVar(),
            "Valve 7 Substance": tk.StringVar(),
            "Valve 8 Substance": tk.StringVar(),
        }

        # fill the exp_var entry boxes with their default values as configured in self.exp_data
        for key in self.stimuli_entries.keys():
            self.stimuli_entries[key].set(self.stimuli_data.get_default_value(key))

        for key, value in self.stimuli_entries.items():
            value.trace_add(
                "write",
                lambda *args, key=key, value=value: self.stimuli_data.update_model(
                    key, GUIUtils.safe_tkinter_get(value)
                ),
            )

        self.init_content()

        # on init, we just want to create the window so that we don't have to later, but then we want to hide it
        # until the user chooses to show this window
        self.withdraw()

        logger.info("Experiment Control Window created, but hidden for now.")

    def show(self):
        """
        Makes the window visible. Checks if the number of stimuli has changed and rebuilds
        the UI content if necessary before showing the window.
        """
        prev_num_stim = len(self.ui_components["entries"])
        curr_num_stimuli = self.exp_process_data.exp_var_entries["Num Stimuli"]
        if prev_num_stim != curr_num_stimuli:
            self.init_content()
        self.deiconify()

    def generate_button_method(self):
        """
        Handles the 'Generate Schedule' button click. Triggers schedule generation
        in the data model, hides the window, and signals the main application via the trigger callback.
        """
        # generate the program schedule df and fill it with stimuli that will be used
        if not self.exp_process_data.generate_schedule():
            return

        self.withdraw()
        self.trigger("GENERATE SCHEDULE")

    def init_content(self) -> None:
        """
        Initializes or re-initializes the main UI elements of the window.
        Creates the main frame, populates it with stimuli/valve entry fields,
        and adds the 'Generate Schedule' button.
        """
        try:
            # Create the notebook (method of creating tabs at the bottom of the window), and set items to expand in all directions if window is resized
            self.stimuli_frame = ttk.Frame(self)
            self.stimuli_frame.grid(row=1, column=0, sticky="nsew")

            self.populate_stimuli_frame()

            GUIUtils.create_button(
                self,
                "Generate Schedule",
                lambda: self.generate_button_method(),
                "green",
                0,
                0,
            )

            logger.info("Filled contents of experiment control window.")
        except Exception as e:
            logger.error(f"Error filling experiment control window: {e}")
            raise

    def fill_reverse_stimuli(self, source_var: tk.StringVar, mapped_var: tk.StringVar):
        """
        Callback triggered when a stimulus entry's StringVar is modified.
        It reads the new value from the source variable and sets the corresponding
        (mapped) variable on the opposite side to the same value, ensuring that each stimuli is represented
        on both sides of the experiment.

        Parameters
        ----------
        - **source_var** (*tk.StringVar*): The variable that was just changed by the user.
        - **mapped_var** (*tk.StringVar*): The variable for the corresponding valve on the other side.
        """
        try:
            new_value = source_var.get()
            # Update the mapped variable with the new value
            mapped_var.set(new_value)
            logger.debug(f"Filled reverse stimuli: {new_value}")
        except Exception as e:
            logger.error(f"Error filling reverse stimuli: {e}")
            raise

    def populate_stimuli_frame(self) -> None:
        """
        Creates and places the Label and Entry widgets for valve substance assignments
        within the `stimuli_entry_frame`. Organizes entries into 'Side One' and 'Side Two'.
        Sets up trace callbacks to link corresponding valves (1<->5, 2<->6, etc.).
        """
        try:
            row = 1
            self.ui_components: Dict[str, List[tk.Widget]] = {
                "frames": [],
                "labels": [],
                "entries": [],
            }

            self.stimuli_entry_frame = tk.Frame(
                self.stimuli_frame, highlightthickness=2, highlightbackground="black"
            )
            self.stimuli_entry_frame.grid(
                row=0, column=0, pady=5, padx=5, sticky="nsew"
            )
            self.stimuli_entry_frame.grid_rowconfigure(0, weight=1)

            side_one_label = tk.Label(
                self.stimuli_entry_frame,
                text="Side One",
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=2,
                highlightbackground="dark blue",
            )
            side_one_label.grid(row=0, column=0, pady=5)
            side_two_label = tk.Label(
                self.stimuli_entry_frame,
                pady=0,
                text="Side Two",
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=2,
                highlightbackground="dark blue",
            )
            side_two_label.grid(row=0, column=1, pady=5)
            for i in range(self.exp_process_data.exp_var_entries["Num Stimuli"] // 2):
                column = 0

                frame, label, entry = GUIUtils.create_labeled_entry(
                    self.stimuli_entry_frame,
                    f"Valve {i + 1}",
                    self.stimuli_entries[f"Valve {i + 1} Substance"],
                    row,
                    column,
                )

                source_var = self.stimuli_entries[f"Valve {i + 1} Substance"]
                mapped_var = self.stimuli_entries[f"Valve {i + 5} Substance"]

                self.stimuli_entries[f"Valve {i + 1} Substance"].trace_add(
                    "write",
                    lambda name,
                    index,
                    mode,
                    source_var=source_var,
                    mapped_var=mapped_var: self.fill_reverse_stimuli(
                        source_var, mapped_var
                    ),
                )
                self.ui_components["frames"].append(frame)
                self.ui_components["labels"].append(label)
                self.ui_components["entries"].append(entry)

                row += 1

            row = 1
            for i in range(self.exp_process_data.exp_var_entries["Num Stimuli"] // 2):
                column = 1
                frame, label, entry = GUIUtils.create_labeled_entry(
                    self.stimuli_entry_frame,
                    f"Valve {i + 5}",
                    self.stimuli_entries[f"Valve {i + 5} Substance"],
                    row,
                    column,
                )

                source_var = self.stimuli_entries[f"Valve {i + 5} Substance"]
                mapped_var = self.stimuli_entries[f"Valve {i + 1} Substance"]

                self.stimuli_entries[f"Valve {i + 5} Substance"].trace_add(
                    "write",
                    lambda name,
                    index,
                    mode,
                    source_var=source_var,
                    mapped_var=mapped_var: self.fill_reverse_stimuli(
                        source_var, mapped_var
                    ),
                )
                self.ui_components["frames"].append(frame)
                self.ui_components["labels"].append(label)
                self.ui_components["entries"].append(entry)

                row += 1

            logger.info("Stimuli frame populated.")
        except Exception as e:
            logger.error(f"Error populating stimuli frame: {e}")
            raise
