import tkinter as tk
import platform
import logging
from tkinter import ttk
from typing import Dict, List, TYPE_CHECKING, Optional

from gui_utils import GUIUtils

if TYPE_CHECKING:
    from program_control import ProgramController

# Get the logger from the controller
logger = logging.getLogger()

class ExperimentCtlWindow:
    def __init__(self, controller: 'ProgramController'):
        self.controller = controller
        self.system = platform.system()
        self.top: Optional[tk.Toplevel] = None
        self.canvas = None  # Initialize canvas here to ensure it's available for binding
        self.num_tabs = 0

        logger.info("ExperimentCtlWindow initialized.")

    def create_window(self, master) -> tk.Toplevel:
        logger.debug("Creating experiment control window.")
        try:
            self.top = tk.Toplevel(master)
            self.top.title("Stimuli / Valves")
            
            # Safely bind the event using a local variable in the lambda to avoid referencing a potentially None self.top
            top_local = self.top
            top_local.bind("<Control-w>", lambda e: top_local.destroy())
            self.top.resizable(False, False)

            icon_path = self.controller.get_window_icon_path()
            GUIUtils.set_program_icon(self.top, icon_path)

            logger.info("Experiment control window created successfully.")
            return self.top
        except Exception as e:
            logger.error(f"Error creating experiment control window: {e}")
            raise

    def center_window(self, width, height):
        try:
            # Get the screen dimensions
            screen_width = self.top.winfo_screenwidth()
            screen_height = self.top.winfo_screenheight()

            # Calculate the x and y coordinates to center the window
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)

            # Set the window's position
            self.top.geometry(f"{width}x{height}+{x}+{y}")
            logger.debug("Experiment control window centered.")
        except Exception as e:
            logger.error(f"Error centering experiment control window: {e}")
            raise

    def create_labeled_entry(
        self,
        parent: tk.Frame,
        label_text: str,
        text_var: tk.StringVar,
        row: int,
        column: int,
    ) -> tuple[tk.Frame, tk.Label, tk.Entry]:
        try:
            frame = tk.Frame(parent)
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            label = tk.Label(
                frame,
                text=label_text,
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="dark blue",
            )
            label.grid(row=0, pady=10)

            entry = tk.Entry(
                frame,
                textvariable=text_var,
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="black",
            )
            entry.grid(row=1, sticky="nsew")

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(1, weight=1)

            logger.debug(f"Labeled entry created: {label_text}")
            return frame, label, entry
        except Exception as e:
            logger.error(f"Error creating labeled entry '{label_text}': {e}")
            raise

    def fill_reverse_stimuli(self, source_var, mapped_var):
        try:
            new_value = source_var.get()
            mapped_var.set(new_value)  # Update the mapped variable with the new value
            logger.debug(f"Filled reverse stimuli: {new_value}")
        except Exception as e:
            logger.error(f"Error filling reverse stimuli: {e}")
            raise

    def configure_tk_obj_grid(self, obj):
        try:
            # setting the tab to expand when we expand the window
            obj.grid_rowconfigure(0, weight=1)
            obj.grid_columnconfigure(0, weight=1)
            logger.debug("Configured TK object grid.")
        except Exception as e:
            logger.error(f"Error configuring TK object grid: {e}")
            raise

    def show_window(self, master) -> None:
        try:
            # if the number of stimuli is currently set to zero, tell the user that they need to add stimuli before we can move forward
            if self.controller.get_num_stimuli() > 0:
                if self.top is not None and self.top.winfo_exists():
                    self.top.lift()
                else:
                    self.top = self.create_window(master)
                    self.configure_tk_obj_grid(self.top)
                    self.top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event

                    # Create the notebook (method of creating tabs at the bottom of the window), and set items to expand in all directions if window is resized
                    main_frame = ttk.Frame(self.top)
                    main_frame.grid(sticky="nsew")

                    self.populate_stimuli_frame(main_frame)

                    self.button_frame = tk.Frame(main_frame, highlightthickness=2, highlightbackground="black")
                    self.button_frame.grid(row=1, column=0, pady=5, sticky="nsew")
                    self.button_frame.grid_columnconfigure(0, weight=1)
                    self.button_frame.grid_rowconfigure(0, weight=1)

                    # stimuli schedule button that calls the function to generate the program schedule when pressed
                    self.generate_stimulus = tk.Button(
                        self.button_frame,
                        text="Generate Schedule",
                        command=lambda: self.controller.generate_experiment_schedule(),
                        bg="green",
                        font=("Helvetica", 24),
                    )
                    self.generate_stimulus.grid(row=0, column=0, pady=5, padx=5, sticky="nsew")

                    self.top.update_idletasks()
                    window_width = self.top.winfo_reqwidth()
                    window_height = self.top.winfo_reqheight()
                    self.center_window(window_width, window_height)  # Center the window on the screen

                logger.info("Experiment control window shown.")
            else:
                logger.warning("Cannot show experiment control window: number of stimuli is zero.")
        except Exception as e:
            logger.error(f"Error showing experiment control window: {e}")
            raise

    def populate_stimuli_frame(self, tab) -> None:
        try:
            row = 1
            self.ui_components: Dict[str, List[tk.Widget]] = {"frames": [], "labels": [], "entries": []}

            self.stimuli_entry_frame = tk.Frame(tab, highlightthickness=2, highlightbackground="black")
            self.stimuli_entry_frame.grid(row=0, column=0, pady=5, padx=5, sticky="nsew")
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

            for i in range(self.controller.get_num_stimuli() // 2):
                column = 0

                frame, label, entry = self.create_labeled_entry(
                    self.stimuli_entry_frame,
                    f"Valve {i+1}",
                    self.controller.data_mgr.stimuli_vars[f"Valve {i+1} substance"],
                    row,
                    column,
                )

                source_var = self.controller.data_mgr.stimuli_vars[f"Valve {i+1} substance"]
                mapped_var = self.controller.data_mgr.stimuli_vars[f"Valve {i+5} substance"]

                self.controller.data_mgr.stimuli_vars[f"Valve {i+1} substance"].trace_add(
                    "write",
                    lambda name, index, mode, source_var=source_var, mapped_var=mapped_var: self.fill_reverse_stimuli(
                        source_var, mapped_var
                    ),
                )
                self.ui_components["frames"].append(frame)
                self.ui_components["labels"].append(label)
                self.ui_components["entries"].append(entry)

                row += 1

            row = 1
            for i in range(self.controller.get_num_stimuli() // 2):
                column = 1
                frame, label, entry = self.create_labeled_entry(
                    self.stimuli_entry_frame,
                    f"Valve {i+5}",
                    self.controller.data_mgr.stimuli_vars[f"Valve {i+5} substance"],
                    row,
                    column,
                )

                source_var = self.controller.data_mgr.stimuli_vars[f"Valve {i+5} substance"]
                mapped_var = self.controller.data_mgr.stimuli_vars[f"Valve {i+1} substance"]

                self.controller.data_mgr.stimuli_vars[f"Valve {i+5} substance"].trace_add(
                    "write",
                    lambda name, index, mode, source_var=source_var, mapped_var=mapped_var: self.fill_reverse_stimuli(
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

    def reset_traces(self):
        try:
            for var_name, string_var in self.controller.data_mgr.stimuli_vars.items():
                try:
                    traces = string_var.trace_info()
                    for trace in traces:
                        try:
                            mode, cbname = trace[:2]  # Safely unpack
                            string_var.trace_remove(mode, cbname)
                        except (ValueError, IndexError):
                            logger.warning(f"Error removing trace for variable '{var_name}': {trace}")
                except KeyError:
                    logger.warning(f"Variable '{var_name}' not found in stimuli_vars")
                except Exception as e:
                    logger.error(f"Error processing variable '{var_name}': {e}")
            logger.info("Traces reset.")
        except Exception as e:
            logger.error(f"Error resetting traces: {e}")
            raise

    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        try:
            if self.top is not None:
                self.top.destroy()
                self.top = None
                logger.info("Experiment control window closed.")
        except Exception as e:
            logger.error(f"Error closing experiment control window: {e}")
            raise
            
    def close_window(self) -> None:
        try:
            if self.top is not None: 
                self.top.destroy()
                logger.info("Experiment control window closed.")
        except Exception as e:
            logger.error(f"Error closing experiment control window: {e}")
            raise
