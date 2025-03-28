"""
This module is used to locate files on the current PC regardless of OS, user, etc.
Useful for finding application documents like the configuration .toml files and program icon at the
Photologic-Experiment-Rig-Files directory under the users documents folder.
"""

import os
import platform


def get_documents_dir():
    """
    This method grabs the documents directory for the current user of the PC in use.
    """
    current_os = platform.system()

    if current_os == "Windows":
        return os.path.join(os.getenv("USERPROFILE"), "Documents")
    elif current_os == "Linux":
        return os.path.join(os.getenv("HOME"), "Documents")


def get_assets_path():
    """
    This method grabs the assets directory under the Photologic-Experiment-Rig-Files directory for current user of the PC in use.
    Grabs documents folder first, then Photologic-Experiment-Rig-Files, then assets. Useful to grab rat.ico and config files.
    """
    documents_dir = get_documents_dir()

    assets_dir = os.path.join(
        documents_dir, "Photologic-Experiment-Rig-Files", "assets"
    )
    return assets_dir


def get_rig_config():
    """
    utilizes previous methods to grab the rig configuration toml file.
    """
    documents_dir = get_documents_dir()

    toml_config_path = os.path.join(
        documents_dir, "Photologic-Experiment-Rig-Files", "assets", "rig_config.toml"
    )
    return toml_config_path


def get_log_path(file_name: str):
    """
    utilizes previous methods to grab the logfile directory.
    """
    documents_dir = get_documents_dir()

    log_dir = os.path.join(documents_dir, "Photologic-Experiment-Rig-Files", "logfiles")

    logfile_path = os.path.join(log_dir, f"{file_name}.txt")

    return logfile_path


def get_valve_durations():
    """
    utilizes previous methods to grab the valve duration configurtion toml file. this is used to store durations long term for the Arduino.
    """
    documents_dir = get_documents_dir()

    log_dir = os.path.join(documents_dir, "Photologic-Experiment-Rig-Files", "assets")

    durations_path = os.path.join(log_dir, "valve_durations.toml")

    return durations_path
