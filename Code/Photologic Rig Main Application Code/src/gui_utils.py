import platform
from tkinter import PhotoImage

class GUIUtils:
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
