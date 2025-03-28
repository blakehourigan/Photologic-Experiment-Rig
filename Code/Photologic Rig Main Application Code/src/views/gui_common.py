"""
This module defines the GUIUtils class, a collection of static helper methods
designed to simplify the creation and management of common Tkinter GUI elements
used across the application's views.

It provides standardized ways to build widgets like labeled entries, buttons,
and frames, as well as utility functions for error display, icon handling,
safe variable access, and window positioning.
"""

import tkinter as tk

from tkinter import PhotoImage
import platform
import os
from tkinter import messagebox
import logging
from typing import Callable

import system_config

logger = logging.getLogger()


class GUIUtils:
    """
    Provides static utility methods for common GUI-related tasks in Tkinter.

    This class bundles functions frequently needed when building Tkinter interfaces.
    Designed to aid in code reuse and consistency across different view (GUI) components. Since all
    methods are static, this class is not intended to be instantiated; its methods
    should be called directly using the class name (e.g., `GUIUtils.create_button(...)`).

    Attributes
    ----------
    None (all methods are static).

    Methods
    -------
    - `create_labeled_entry(...)`
        Creates a standard Lable/Entry combination component packed in a shared Frame.
    - `create_basic_frame(...)`
        Creates a basic Frame widget with grid expansion configuration.
    - `create_button(...)`
        Creates a standard Button widget within a Frame.
    - `display_error(...)`
        Shows a error message box to the user.
    - `create_timer(...)`
        Creates a timer label wiget.
    - `get_window_icon_path()` -> *could be moved to `system_config` module later.*
        Determines and returns the OS-specific path for the application icon.
    - `set_program_icon(...)`
        Sets the icon for a given Tkinter window based on the OS.
    - `safe_tkinter_get(...)`
        Safely retrieves the value from a Tkinter variable, handling potential errors when stored value is "" or nothing.
    - `center_window(...)`
        Positions a Tkinter window in the center of the screen.
    - `askyesno(...)`
        Displays a standard yes/no confirmation dialog box.
    """

    @staticmethod
    def create_labeled_entry(
        parent: tk.Frame,
        label_text: str,
        text_var: tk.IntVar | tk.StringVar,
        row: int,
        column: int,
    ) -> tuple[tk.Frame, tk.Label, tk.Entry]:
        """
        Creates a standard UI component consisting of a Frame containing a Label
        positioned above an Entry widget. Configures grid weighting for resizing.

        Parameters
        ----------
        - **parent** (*tk.Frame*): The parent widget where this component will be placed.
        - **label_text** (*str*): The text to display in the Label widget.
        - **text_var** (*tk.IntVar OR tk.StringVar*): The Tkinter variable linked to the Entry widget's content.
        - **row** (*int*): The grid row within the parent widget for this component's frame.
        - **column** (*int*): The grid column within the parent widget for this component's frame.

        Returns
        -------
        - *tuple[tk.Frame, tk.Label, tk.Entry]*: A tuple containing the created created Frame, Label, and Entry widgets.

        Raises
        ------
        - *Exception*: Propagates any exceptions that occur during widget creation, after logging the error.
        """
        try:
            frame = tk.Frame(parent)
            frame.grid(row=row, column=column, padx=5, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_rowconfigure(1, weight=1)

            label = tk.Label(
                frame,
                text=label_text,
                bg="light blue",
                font=("Helvetica", 20),
                highlightthickness=1,
                highlightbackground="dark blue",
            )
            label.grid(row=0, pady=5)

            entry = tk.Entry(
                frame,
                textvariable=text_var,
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="black",
            )
            entry.grid(row=1, sticky="nsew", pady=5)

            logger.info(f"Labeled entry '{label_text}' created.")
            return frame, label, entry
        except Exception as e:
            logger.error(f"Error creating labeled entry '{label_text}': {e}")
            raise

    @staticmethod
    def create_basic_frame(
        parent: tk.Frame | tk.Tk, row: int, column: int, rows: int, cols: int
    ) -> tk.Frame:
        """
        Creates a basic tk.Frame widget with optional highlighting and grid configuration.

        Parameters
        ----------
        - **parent** (*tk.Frame OR tk.Tk, tk.Toplevel]*): The parent widget.
        - **row** (*int*): The grid row for the frame in the parent.
        - **column** (*int*): The grid column for the frame in the parent.
        - **rows** (*int, optional*): Number of internal rows to configure with weight=1 / expansion.
        - **cols** (*int, optional*): Number of internal columns to configure with weight=1 / expansion.

        Returns
        -------
        - *tk.Frame*: The created and configured Frame widget.

        Raises
        ------
        - *Exception*: Propagates any exceptions during frame creation, after logging.
        """
        try:
            frame = tk.Frame(parent, highlightthickness=1, highlightbackground="black")
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
            for i in range(rows):
                frame.grid_rowconfigure(i, weight=1)
            for i in range(cols):
                frame.grid_columnconfigure(i, weight=1)

            return frame
        except Exception as e:
            logger.error(f"Error creating status frame: {e}")
            raise

    @staticmethod
    def create_button(
        parent: tk.Frame,
        button_text: str,
        command: Callable,
        bg: str,
        row: int,
        column: int,
    ) -> tuple[tk.Frame, tk.Button]:
        """
        Creates a tk.Button widget housed within its own tk.Frame for layout control.

        The Frame allows the button to expand/contract cleanly within its grid cell.

        Parameters
        ----------
        - **parent** (*Union[tk.Frame, tk.Tk, tk.Toplevel]*): The parent widget.
        - **button_text** (*str*): The text displayed on the button.
        - **command** (*Callable / Function*): The function or method to call when the button is clicked.
        - **bg** (*str*): The background color of the button (Tkinter colors e.g., "green", "light grey").
        - **row** (*int*): The grid row for the button's frame in the parent.
        - **column** (*int*): The grid column for the button's frame in the parent.

        Returns
        -------
        - *tuple[tk.Frame, tk.Button]*: A tuple containing the created Frame and Button widgets.

        Raises
        ------
        - *Exception*: Propagates any exceptions during widget creation, after logging.
        """
        try:
            frame = tk.Frame(parent, highlightthickness=1, highlightbackground="black")
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            button = tk.Button(
                frame, text=button_text, command=command, bg=bg, font=("Helvetica", 24)
            )
            button.grid(row=0, sticky="nsew", ipadx=10, ipady=10)

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            logger.info(f"Button '{button_text}' created.")
            return frame, button
        except Exception as e:
            logger.error(f"Error creating button '{button_text}': {e}")
            raise

    @staticmethod
    def display_error(error: str, message: str) -> None:
        """
        Displays an error message box to the user.

        Parameters
        ----------
        - **error_title** (*str*): The title for the error message box window.
        - **message** (*str*): The error message content to display.

        Raises
        ------
        - *Exception*: Propagates any exceptions from messagebox, after logging.
        """
        try:
            messagebox.showinfo(error, message)
            logger.error(f"Error displayed: {error} - {message}")
        except Exception as e:
            logger.error(f"Error displaying error message: {e}")
            raise

    @staticmethod
    def create_timer(
        parent: tk.Frame | tk.Tk | tk.Toplevel,
        timer_name: str,
        initial_text: str,
        row: int,
        column: int,
    ):
        """
        Creates a UI component for displaying a tkinter Label component serving as timer, consists of a Frame
        containing a timer name Label and a time display Label.

        Parameters
        ----------
        - **parent** (*tk.Frame OR tk.Tk OR tk.Toplevel]*): The parent widget.
        - **timer_name** (*str*): The descriptive name for the timer (e.g., "Session Time").
        - **initial_text** (*str*): The initial text to display in the time label (e.g., "00:00:00").
        - **row** (*int*): The grid row for the timer's frame in the parent.
        - **column** (*int*): The grid column for the timer's frame in the parent.

        Returns
        -------
        - *Tuple[tk.Frame, tk.Label, tk.Label]*: A tuple containing the Frame, the name Label,
          and the time display Label.

        Raises
        ------
        - *Exception*: Propagates any exceptions during widget creation, after logging.
        """
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
                frame, text=initial_text, bg="light blue", font=("Helvetica", 24)
            )
            time_label.grid(row=0, column=1)

            logger.info(f"Timer '{timer_name}' created.")
            return frame, label, time_label
        except Exception as e:
            logger.error(f"Error creating timer '{timer_name}': {e}")
            raise

    @staticmethod
    def get_window_icon_path() -> str:
        """
        Determines the correct application icon file path based on the operating system.

        Relies on `system_config.get_assets_path()` to find the assets directory.
        Uses '.ico' for Windows and '.png' for other systems (Linux, macOS).

        Returns
        -------
        - *str*: The absolute path to the appropriate icon file.

        Raises
        ------
        - *FileNotFoundError*: If the determined icon file does not exist.
        - *Exception*: Propagates exceptions from `system_config` or `os.path`.
        """
        # get the absolute path of the assets directory
        base_path = system_config.get_assets_path()

        # Determine the operating system
        os_name = platform.system()

        # Select the appropriate icon file based on the operating system
        if os_name == "Windows":
            # Windows expects .ico
            icon_filename = "rat.ico"
        else:
            # Linux and macOS use .png
            icon_filename = "rat.png"

        return os.path.join(base_path, icon_filename)

    @staticmethod
    def set_program_icon(window: tk.Tk | tk.Toplevel, icon_path: str) -> None:
        """
        Sets the program icon for a given Tkinter window (Tk or Toplevel).

        Uses the appropriate method based on the operating system (`iconbitmap` for
        Windows, `iconphoto` for others).

        Parameters
        ----------
        - **window** (*tk.Tk OR tk.Toplevel*): The Tkinter window object whose icon should be set.
        - **icon_path** (*str*): The absolute path to the icon file ('.ico' for Windows, '.png'/''.gif' otherwise).

        Raises
        ------
        - *Exception*: Propagates any exceptions during icon setting, after logging.
        """
        os_name = platform.system()
        if os_name == "Windows":
            window.iconbitmap(icon_path)
        else:
            # Use .png or .gif file directly
            photo = PhotoImage(file=icon_path)
            window.tk.call("wm", "iconphoto", window._w, photo)  # type: ignore

    @staticmethod
    def safe_tkinter_get(var: tk.StringVar | tk.IntVar) -> str | int | None:
        """
        Safely retrieves the value from a Tkinter variable using .get().
        .get() method fails on tk int values
        when the value is "" or empty (when emptying a entries contents and filling it
        with something else), this avoids that by returning none instead if the val is == "".

        Specifically handles the `tk.TclError` that occurs when trying to `.get()` an
        empty `tk.IntVar` or `tk.DoubleVar` (often happens when an Entry linked
        to it is cleared by the user). Returns `None` in case of this error.

        Parameters
        ----------
        - **var** (*str OR int or None*): The Tkinter variable to get the value from.

        Raises
        ------
        - *Exception*: Propagates any non-TclError exceptions during the `.get()` call.
        """
        try:
            return var.get()
        except tk.TclError:
            return None

    @staticmethod
    def center_window(window: tk.Tk | tk.Toplevel) -> None:
        """
        Centers a Tkinter window on the screen based on screen dimensions. Specifically, window has maximum of 80 percent of screen
        width and height.

        Forces an update of the window's pending tasks (`update_idletasks`) to ensure
        its requested size (`winfo_reqwidth`, `winfo_reqheight`) is accurate before calculating
        the centering position. Sets the window's geometry string.

        Parameters
        ----------
        - **window** (*tk.Tk OR tk.Toplevel*): The window object to center.

        Raises
        ------
        - *Exception*: Propagates any exceptions during geometry calculation or setting, after logging.
        """
        try:
            # Get the screen dimensions
            window_width = window.winfo_reqwidth()
            window_height = window.winfo_reqheight()

            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            max_width = int(window_width * 0.80)
            max_height = int(window_height * 0.80)

            # Calculate the x and y coordinates to center the window
            x = (screen_width - max_width) // 2
            y = (screen_height - max_height) // 2

            # Set the window's position
            window.geometry(f"{max_width}x{max_height}+{x}+{y}")

            logger.info("Experiment control window re-sized centered.")
        except Exception as e:
            logger.error(f"Error centering experiment control window: {e}")
            raise

    @staticmethod
    def askyesno(window_title: str, message: str) -> bool:
        """
        Displays a standard modal confirmation dialog box with 'Yes' and 'No' buttons.

        Wraps `tkinter.messagebox.askyesno`.

        Parameters
        ----------
        - **window_title** (*str*): The title for the confirmation dialog window.
        - **message** (*str*): The question or message to display to the user.

        Returns
        -------
        - *bool*: `True` if the user clicks 'Yes', `False` if the user clicks 'No' or closes the dialog.

        Raises
        ------
        - *Exception*: Propagates any exceptions from messagebox, after logging.
        """
        return messagebox.askyesno(title=window_title, message=message)
