# Samuelsen Lab Photologic-Experiment-Rig

## Overview
This project was created to enable novel experiments regarding smell and taste in Dr. Chad Samuelsen's research laboratory. The primary improvements that this rig provide include a photologic lick detection mechanism, and a simplified, non-motorized approach to stimulus delivery providing a more reliable experience during experimentation. 

This repository contains all files needed to reproduce a experimental rig of this type, including all 3d models, CNC machining files, code, and circuit design. 

## Features

- Accurate data retreival


### Required Physical Materials


- prerequisites 

### Assembly Instructions / Requirements for a Functioning Rig
1. **Rig Controller Code**
    #### Prerequisites / Dependencies
    To use this program with the Arduino board controlling the rig peripherals (motors, optical sensors, etc) on a Windows machine, you **must** have the Arduino IDE installed. Failing to meet this dependency will result in the Arduino boards failure to connect to the controlling computer. 
    
    #### Windows Installation 
    To install the program on windows, there are two options. 
    
    1. **.exe Installer File** - To simplify this portion of the rig assembly / installation, a simple .exe installer has been provided. It can be found [here]().
    
    2. **Running the Source Code** - For those that would rather run the program via source code, the process for getting the source code up and running can be found below.
        1. **Install Python 3.12** - This program was developed with Python version 3.12. This program is NOT guaranteed to work with any versions other than Python3.12. It can be installed [here](https://www.python.org/downloads/release/python-3120/).
        2. **Clone this repository locally on your computer** - Either by using git clone on your machine, or by clicking the 'code' dropdown on the homepage of this Github repo and downloading the .zip file, download this repository onto your machine.
        3. **Setup the Virtual Environment** - Once you have the repo locally on your machine, navigate to the controller code directory at `Photologic-Experiment-Rig\Code\Photologic Rig Main Application Code`. Once here, you can setup a virtual environment that will contain all depencies for the program by running the following command in a terminal window at this directory: `python -m venv venv'. This may take a few moments.
        4. **Activate the Environment** - Once the virtual environment is setup, you can activate it by running the following command.
            - **Windows** -> `venv\Scripts\Activate`
            - **Linux** -> `source venv/bin/activate `
        6. **Install the Dependencies** - This program is dependent on many external libraries to function properly. Under the 'Photologic Rig Main Application Code' directory, you will also find a file called requirements.txt. It contains all depencencies and their versions in a simple text file. You can install all of these dependencies at once by running the command `pip install -r requirements.txt`.
        7. **Run the Program** - You are now ready to run the controller program. Locate the file 'main.py' under the /src directory and run it by running the command `python main.py`, the program should now startup.


    #### Running the Program on Linux-based Systems
    There is no installation file for linux-based systems. Follow the 'Running the Source Code' steps described above.
    
2. **Arduino Code Installation/Upload**
    #### Prerequisites / Dependencies
    To upload this code, you will need either the arduino-cli or the Arduino IDE. The Arduino IDE will be easiest to work with and can be found [here](https://www.arduino.cc/en/software).
 
5. **3D Printing:**   3d print instruc
6. **Machining:**   machining parts 
7. **Assembly:**   assembly instruc
8. **Optical Fiber Setup:**   fiber instruc
9. **Circuitry:** Circuitry details / instructions


### Configuration

how to configure the system once assembled.

## Usage
A **SOP** (Standard Operating Procedure) for using this rig in an experiment can be found [here]().


## Navigating the Directory Structure
- **CAD Files:** All CAD files for 3D printing and machining.
- **Code:** The code directory contains all code written for this project. The primary sub-directory here is the 'Photologic Rig Main Application Code' directory which contains the rig controller applcation code to be executed on the lab desktop connected to the arduino boards. The structure of this program was designed with the intention of being easy to understand and modify. It follows a model-view-controller model in principle where 'model' refers to the data structures of the program, view refers to all graphical user interface (GUI) related code, and controller refers to the code that coordinates operations requiring both of these aspects of the program. This should make the task of searching for code performing specific functions simpler. For example, the code that generates the schedule of stimuli for the experiment can be found at 'models/experiment_process_data.py' becuase the methods that implement this functionality operate directly on data related to the process of the experiment. Stimulus related data such as the stimuli substance names can be found at 'models/stimuli_data.py'. It is my hope that this design simplifies the experience of working with this code for future users and maintainers.

## License

This project is licensed under the MIT License - see LICENSE.txt for details.


  
- **Documentation:** Detailed documents and instructions.
- **Example:** Images and examples of the final assembled product.
- **Circuitry:** Diagrams and files related to the electrical components.
