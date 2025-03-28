"""
This module defines the EventWindow class, a tkinter Toplevel window used to display timestamps
and other details for experiment event data (licks, motor movments) in a table format using a ttk.Treeview element.
"""

import tkinter as tk
from tkinter import ttk

#### USED FOR TYPE HINTS ####
from models.event_data import EventData
#### USED FOR TYPE HINTS ####

from views.gui_common import GUIUtils


class EventWindow(tk.Toplevel):
    """
    This class represents a Toplevel window that displays experiment event data using a ttk.Treeview widget.
    It pulls in data from an `models.event_data` `EventData` instance and is updated as new events occur.
    After creation, window is hidden and can be shown using the `show`() method.

    Attributes
    ----------
    - **event_data** (*EventData*): A reference to the data model instance (`models.event_data.EventData`)
      that holds the event DataFrame containing the data to be displayed.
    - **last_item** (*int*): Tracks the index of the last row added from the DataFrame to the Treeview.
      This is used to efficiently update the table by only adding new rows.
    - **licks_frame** (*tk.Frame*): The main tkinter Frame widget within the window that contains the Treeview table.
    - **timestamped_events** (*ttk.Treeview*): The Treeview widget used to display the event data in a table format.

    Methods
    -------
    - `show`()
        Updates the table with the latest data from the `event_data` model and makes the window visible (deiconifies it).
    - `update_table`()
        Efficiently adds new rows from the event DataFrame (held by `event_data`) to the Treeview display. It only adds rows
        that haven't been added previously, based on the `last_item` attribute.
    - `build_table`()
        Creates the main frame (`licks_frame`) and the `ttk.Treeview` widget (`timestamped_events`). Configures the Treeview columns
        and headings based on the columns present in the `event_data.event_dataframe`.
    """

    # inject the event dataframe when we create the class so we have access to that data
    def __init__(self, event_data: EventData) -> None:
        """
        Initialize the EventWindow. Sets up the window title, icon, key bindings (Ctrl+W to hide),
        and the close protocol (also hides the window). It builds the table structure and initially
        hides the window using `withdraw()`.

        Parameters
        ----------
        - **event_data** (*EventData*): An instance of the `models.event_data.EventData` model containing the
          event DataFrame to be displayed.
        """
        super().__init__()
        # reference to event model
        self.event_data = event_data

        self.title("Experiment Event Data")
        self.bind("<Control-w>", lambda event: self.withdraw())

        # Bind closing the window to self.withdraw() to hide the window but not destroy it
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

        # init last_item in the table to zero we haven't added anything into the table
        # this is used to efficiently update the table when program is running
        self.last_item = 0

        self.build_table()

        self.withdraw()

    def show(self):
        """
        Updates the table with the latest event data and makes the window visible.
        Calls `update_table()` first, then `deiconify()` to show the window.
        """
        self.update_table()
        self.deiconify()

    def update_table(self):
        """
        Updates the Treeview widget by adding only the new rows from the event DataFrame
        since the last update. It uses `self.last_item` to determine the starting index
        for adding new rows, ensuring efficient updates without reprocessing existing entries.
        """
        # df we are working with is self.event_data.event_dataframe, get rid of self prefix and such to save room
        df = self.event_data.event_dataframe
        # num rows in that df currently
        len_event_df = len(df)

        last_item = self.last_item

        # Insert data from the DataFrame. iterrows() returns an iterator over the rows of a df of form (index, series (of data))
        for i in range(last_item, len_event_df):
            row_content = df.iloc[i]

            item_iid = f"item {i}"

            self.timestamped_events.insert(
                "", tk.END, iid=item_iid, values=list(row_content)
            )
        # update the last item with the LAST item that was added on this iteration, next time we will start
        # the loop with this, so that we don't unneccesarily update entries already there
        self.last_item = len(df)

    def build_table(self) -> None:
        """
        Creates the main frame (`licks_frame`) and the `ttk.Treeview` widget (`timestamped_events`)
        used to display the event data. Configures the Treeview columns and headings based on the
        columns present in the `event_data.event_dataframe`. Calls `update_table()` to initially
        populate the table.
        """
        self.licks_frame = tk.Frame(self)
        self.licks_frame.grid(row=0, column=0, sticky="nsew")

        # Create a Treeview widget
        # show='headings' ensures we only see columns with headings defined
        self.timestamped_events = ttk.Treeview(
            self.licks_frame, show="headings", height=25
        )

        self.timestamped_events["columns"] = list(
            self.event_data.event_dataframe.columns
        )

        # Configure the names of the colums to reflect the heaader labels
        for col in self.timestamped_events["columns"]:
            self.timestamped_events.heading(col, text=col)

        self.update_table()

        self.timestamped_events.pack(fill="both", expand=True)
