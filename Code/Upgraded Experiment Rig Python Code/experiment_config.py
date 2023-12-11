from pathlib import Path
import os
import platform

class Config:
    def __init__(self) -> None:
        self.script_path = Path(__file__).resolve().parent

    def get_window_icon_path(self) -> str:
        # get directory path of project folder
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Determine the operating system
        os_name = platform.system()
        
        # Select the appropriate icon file based on the operating system
        if os_name == 'Windows':
            # Windows expects .ico
            icon_filename = 'rat.ico'
        else:
            # Linux and macOS use .png
            icon_filename = 'rat.png'  

        return os.path.join(base_path, 'assets', icon_filename)
