# Samuelsen Lab Photologic-Experiment-Rig

## Overview
This project was created to enable novel experiments regarding smell and taste in Dr. Chad Samuelsen's research laboratory. The primary improvements that this rig provide include a photologic lick detection mechanism, and a simplified, non-motorized approach to stimulus delivery providing a more reliable experience during experimentation. 

This repository contains all files needed to reproduce a experimental rig of this type, including all 3d models, CNC machining files, code, and circuit design. 

## Features
-  **Data Accuracy** - Important event timing data such as onset, end, duration, onset relative to program start, and onset relative to trial start is measured **on Arduino Mega 2560 device** as these events occur. This ensured event timing results are accurate as viewed in the controller program.
-  **Data Representation** - Licks can be analyzed via a built in lick rasterization plot. This allows for simple visual verification of lick times relative to one another. One can ensure that licks are not occuring too close or too far apart in time. 
-  **Individual Valve / Motor Control** - Users can control each connected valve, opening or closing valves for arbitrary amounts of time. Users can also command the door motor to move up or down at any time. 
-  **Lick/Valve Prohibition** - Lick detection and valve actuation are decoupled events. A lick initiates a valve actuation, however, another lick CANNOT be detected until BOTH the valve has been closed from previous actuation AND tongue has cleared the beam (beam has restored a connection). This helps to avoid licks from occuring too close in succession. Furthermore, a continued beam break does not result in a continuous stream from a valve. A lick initiation will result in a valve opening of the determined length. This will not happen again until beam is restored and broken again. 
-  **Phantom Lick Removal** - Licks that complete in less than 10ms are disregarded and not sent to the controller (PC). This helps avoid invalid licks (due to equipment quirks) being recorded.  
-  **Simplicity** - Significant effort has been expended to ensure that software is easy to install and use. The previous model of using two Arduino boards to control the rig was found to be unnecessary. It was found to be far more effiecient to move to a one Arduino model, simplifying physical setup and communication protocols. 
-  **Speed** - Multiple threads (many cpu workers) are utilized so that GUI is always responsive regardless of logic operations underway at a given moment, without affecting the efficiency of those logic operations. 


### Required Physical Materials

- 1 Arduino Mega 2560
- 1 PC Controller Computer
- 1 Motor Logic Circuit Board
- 1 Experiment Box (3D CAD and CNC files included in this repository)
- 2 - 16 Valves and Cylinders 
 
### Assembly Instructions / Requirements for a Functioning Rig
1. **Rig Controller Code**
    #### Prerequisites / Dependencies
    To use this program with the Arduino board controlling the rig peripherals (motors, optical sensors, etc) on a Windows machine, you **must** have the Arduino IDE installed. Failing to meet this dependency will result in the Arduino boards failure to connect to the controlling computer. 
    
    #### Windows Installation 
    To install the program on windows, there are two options. 
    
    1. **Exe Installer File** - To simplify this portion of the rig assembly / installation, a simple .exe installer has been provided. It can be found [here]().
    
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

    #### Building an Executable for a New Version of the Program
    For those that create new versions of the program to better suit their needs or to fix bugs that will undoubdedly arise through the usage of this program, a [Github Gist](https://gist.github.com/blakehourigan/5e176f2600446a793547babff372299c) has been put together detailing the steps you can take to create a new executable file and installer that will make installation/distribution of the program much simpler. 
    
2. **Arduino Code**
    #### Prerequisites / Dependencies
    To upload this code, you will need either the arduino-cli or the Arduino IDE. The Arduino IDE will be easiest to work with and can be found [here](https://www.arduino.cc/en/software).

    On Windows machines, the Arduino IDE is an optional package in the control software Exe installer discussed above.

    If you choose to use the Arduino IDE, you must follow these steps to ensure smooth upload of this code to the Arduino, and proper communication between the Arduino and the control software.
    #### IDE Configuration and Code Upload
    1. Once the Arduino IDE is installed, open the IDE with the Arduino Mega 2560 board connected to your PC. Your PC will recognize the board and the packages that it needs to install to communicate with it. There will be multiple pop-up windows asking if you would like to install drivers for this board. You **must** click install on all of these pop-ups. If you do not see these pop-ups and have used your Arduino board previously, you may have these packages already installed, try moving to the next step. 
    2. The code used for the Arduino in this project has one external dependency that must be fulfilled. This external dependency is the **AccelStepper** library by Mike McCauley. The version in use at the time of writing is version 1.64. You will need to install this version in the IDE. To do this, look for the library icon on the left hand side of the Arduino IDE window. It is the third button down. Once clicked, a slide-out window with the heading 'library manager' will open with a search box at the top. Click inside of the search bar and enter 'AccelStepper'. The first result should be the one you are looking for. Click the box filled with the version number (something like 1.64), and look for version 1.64. Click on this version, then click install, it should install rather quickly. Now you can now exit the library manager.
    3. Now, the Arduino code may be uploaded to the board. In the top left hand corner, click 'File', then 'Open', and search for the ArduinoCode directory in the Photologic-Experiment-Rig structure. The file you are looking for will be found at `Photologic-Experiment-Rig/Code/ArduinoCode/ArduinoCode.ino`. Locate this .ino file and double click on it to select it.
    4. Once this file is open in the IDE, ensure that your board is recognized and selected in the IDE by clicking the dropdown menu just below the 'help' section of the top bar. Here you will see any Arduino boards recognized by the PC. Select your Arduino Mega 2560 board.
    5. With the file open and your board selected, press the green upload button. It is the arrow that looks like this: '-->', the second button of three in the top left hand side of your screen. This will just take a moment, and you will see a 'Done Uploading' message in the bottom right of your screen if it completes successfully.

       **NOTE** - If you see lots of red messages and this code does not upload successfully, please make absolutely sure you installed the 'ArduinoStepper' library and that the board is connected **and** selected. You might try the board selection dropdown again to make sure of this. If this does not work, try disconnecting and reconnecting the board, and restarting your PC. 
    7. At this point your Arduino board and your PC are ready to communicate with each other for your experiments. 
 
3. **3D Printing:**

   Under contruction

4. **Machining:**   

   Under Contruction 

5. **Assembly:** 

   Under contruction

6. **Optical Fiber Setup:**   

   Under contruction

7. **Circuitry:** 

   Under contruction 

### Configuration

how to configure the system once assembled.

## Usage
A **SOP** (Standard Operating Procedure) for using this rig in an experiment can be found [here]().

## Navigating the Directory Structure
Each subdirectory in this project contains a README that explains the structure of the files contained within.

## License

This project is licensed under the MIT License - see LICENSE.txt for details.
