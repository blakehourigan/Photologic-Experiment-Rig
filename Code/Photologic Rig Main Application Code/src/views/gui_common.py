import tkinter as tk
from tkinter import PhotoImage
import platform
import os
from tkinter import messagebox
import logging

logger = logging.getLogger()


class GUIUtils:
    """
    This class contains helper methods that do not require an instance of self to function. They assist in the creation of
    GUI elements in various GUI (view) classes
    """

    @staticmethod
    def create_labeled_entry(
        parent: tk.Frame,
        label_text: str,
        text_var: tk.IntVar,
        row: int,
        column: int,
    ) -> tuple[tk.Frame, tk.Label, tk.Entry]:
        try:
            frame = tk.Frame(parent)
            frame.grid(row=row, column=column, padx=5, sticky="nsew")

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
            logger.info(f"Labeled entry '{label_text}' created.")
            return frame, label, entry
        except Exception as e:
            logger.error(f"Error creating labeled entry '{label_text}': {e}")
            raise

    @staticmethod
    def create_button(parent, button_text, command, bg, row, column):
        try:
            frame = tk.Frame(parent, highlightthickness=1, highlightbackground="black")
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            button = tk.Button(
                frame, text=button_text, command=command, bg=bg, font=("Helvetica", 24)
            )
            button.grid(row=0, sticky="nsew", ipadx=10, ipady=10)

            frame.grid_columnconfigure(0, weight=1)
            logger.info(f"Button '{button_text}' created.")
            return frame, button
        except Exception as e:
            logger.error(f"Error creating button '{button_text}': {e}")
            raise

    @staticmethod
    def display_error(error, message):
        try:
            messagebox.showinfo(error, message)
            logger.error(f"Error displayed: {error} - {message}")
        except Exception as e:
            logger.error(f"Error displaying error message: {e}")
            raise

    @staticmethod
    def create_timer(parent, timer_name, default_text, row, column):
        try:
            frame = tk.Frame(
                parent, highlightthickness=1, highlightbackground="dark blue"
            )
            frame.grid(row=row, column=column, padx=10, pady=5, sticky="nsw")

            label = tk.Label(
                frame, text=timer_name, bg="light blue", font=("Helvetica", 24)
            )
            label.grid(row=0, column=0)

            time_label = tk.Label(
                frame, text=default_text, bg="light blue", font=("Helvetica", 24)
            )
            time_label.grid(row=0, column=1)

            logger.info(f"Timer '{timer_name}' created.")
            return frame, label, time_label
        except Exception as e:
            logger.error(f"Error creating timer '{timer_name}': {e}")
            raise

    @staticmethod
    def get_window_icon_path() -> str:
        # get the absolute path of two directories above the file from which this file is called
        # we need to get to the assets folder at photologic exp rig/assets and are currently in
        # photologic exp rig/src/views. need to go up twice then down to assets, which is what we do here
        base_path = os.path.dirname(
            os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
        )

        # Determine the operating system
        os_name = platform.system()

        # Select the appropriate icon file based on the operating system
        if os_name == "Windows":
            # Windows expects .ico
            icon_filename = "rat.ico"
        else:
            # Linux and macOS use .png
            icon_filename = "rat.png"

        return os.path.join(base_path, "assets", icon_filename)

    @staticmethod
    def set_program_icon(window, icon_path):
        """Set the program icon for a Tkinter window."""
        os_name = platform.system()
        if os_name == "Windows":
            window.iconbitmap(icon_path)
        else:
            # Use .png or .gif file directly
            photo = PhotoImage(file=icon_path)
            window.tk.call("wm", "iconphoto", window._w, photo)  # type: ignore

    @staticmethod
    def safe_tkinter_get(var):
        """
        static helper method that allows for safe access of tkinter
        variable values via the .get() method. This method fails on tk int values
        when the value is "" or empty (when emptying a entries contents and filling it
        with something else), this avoids that by returning none instead if the val is == ""
        """
        try:
            return var.get()
        except tk.TclError:
            return None

    @staticmethod
    def center_window(window):
        try:
            # Get the screen dimensions
            window_width = window.winfo_reqwidth()
            window_height = window.winfo_reqheight()

            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            # Calculate the x and y coordinates to center the window
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            # Set the window's position
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            logger.info("Experiment control window centered.")
        except Exception as e:
            logger.error(f"Error centering experiment control window: {e}")
            raise

    @staticmethod
    def askyesno(window_title, message) -> bool:
        """
        asks the user a question in a popup window. returns true if yes, false if no
        """
        return tk.messagebox.askyesno(title=window_title, message=message)
