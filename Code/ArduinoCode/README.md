# Arduino Source Code Directory

## Overview

This directory contains the code designed for the Arduino board that runs the motorized components of the 
photologic experiment rig. All licks, valve actuations, and door motor movements are orchestrated here.

## Directory Structure

An attempt was made to organize this structure such that each major component of the program is easy to find. 

### Project Root 

The project root contains the primary Arduino .ino file (comperable to main.py). This is the entry file of the program,
and can be thought of as the primary 'controller' for the Arduino code. It contains the standard 'setup' and 'loop' code 
included with most Arduino programs. 

The setup method defines input and output pins used throughout the program, while loop is the mainloop that runs continuously 
to listen for commands from the python controller program.

### Src Directory 

This directory contains headers and implementations for all primary aspects of the program. While the root file simply calls
logical functions, these directories and files provide the implementation for all this logic. 

**exp_init** - Contains logic regarding program initialization including receiving important program variables such as 
the valve schedules and opening durations for each side, as well and number of valves in use and number of trials.

**optical_detection** - This directory contains functions that detect breaks and reconnections in the optical beam, as well 
as updating the state of the lick indicator leds.

**reporting** - Here you'll find files that define the structure of the data reporting of the Arduino. It calculates event 
timing and sends it back to the controller program.

**valve_control** - Contains methods for interacting with valves. Includes methods for opening /closing single vs many valves.

**valve_testing** - Contains the logic for valve testing procedure as well as valve priming functionality.


