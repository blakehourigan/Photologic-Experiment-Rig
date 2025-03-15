
import toml
import os 
import platform
from pathlib import Path 


def get_documents_dir():
    current_os = platform.system()

    if current_os == 'Windows':

         return os.path.join(os.getenv('USERPROFILE'), 'Documents')
    elif current_os =='Linux':
        return os.path.join(os.getenv('HOME'), 'Documents')

def get_rig_config():
    documents_dir = get_documents_dir()

    toml_config_path = os.path.join(documents_dir, "Photologic-Experiment-Rig-Files", "assets", "rig_config.toml")
    return toml_config_path

def get_log_path(file_name):
    documents_dir = get_documents_dir()

    log_dir = os.path.join(documents_dir,"Photologic-Experiment-Rig-Files","logfiles")

    logfile_path = os.path.join(log_dir,  f"{file_name}.txt")

    return logfile_path

def get_valve_durations():
    documents_dir = get_documents_dir()

    log_dir = os.path.join(documents_dir,"Photologic-Experiment-Rig-Files","assets")
    
    durations_path = os.path.join(log_dir,  "valve_durations.toml")

    return durations_path

    
    