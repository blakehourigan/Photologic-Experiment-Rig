# Samuelsen Lab Photologic-Experiment-Rig

## Overview
This project was created to enable novel experiments regarding smell and taste in Dr. Chad Samuelsen's research laboratory. The primary improvements that this rig provide include a photologic lick detection mechanism, and a simplified, non-motorized approach to stimulus delivery providing a more reliable experience during experimentation. 

This repository contains all files needed to reproduce a experimental rig of this type, including all 3d models, CNC machining files, code, and circuit design. 

## Features


Features


## Installation


Detailed instructions on how to set up the rig. This section is divided into sub-sections for clarity.

### Prerequisites


- prerequisites 

### Assembly Instructions
1. **3D Printing:**   3d print instruc
2. **Machining:**   machining parts 
3. **Assembly:**   assembly instruc
4. **Optical Fiber Setup:**   fiber instruc
5. **Circuitry:** Circuitry details / instructions
6. **Programming:** Downloading and running code

### Configuration


how to configure the system once assembled.

## Usage


usage guide


## License


This project is licensed under the MIT License - see LICENSE.txt for details.

## Acknowledgements


Acknowledging people

## Contact Information

contact details

## Directory Structure
A detailed list of the repository's directory structure, explaining what each folder contains. This helps users navigate the repository more effectively.

- **CAD Files:** All CAD files for 3D printing and machining.
- **Code:** The code directory contains all code written for this project. The primary sub-directory here is the 'Photologic Rig Main Application Code' directory which contains the rig controller applcation code to be executed on the lab desktop connected to the arduino boards. The structure of this program was designed with the intention of being easy to understand and modify. It follows a model-view-controller model in principle where 'model' refers to the data structures of the program, view refers to all graphical user interface (GUI) related code, and controller refers to the code that coordinates operations requiring both of these aspects of the program. This should make the task of searching for code performing specific functions simpler. For example, the code that generates the schedule of stimuli for the experiment can be found at 'models/experiment_process_data.py' becuase the methods that implement this functionality operate directly on data related to the process of the experiment. Stimulus related data such as the stimuli substance names can be found at 'models/stimuli_data.py'. It is my hope that this design simplifies the experience of working with this code for future users and maintainers. 

  
- **Documentation:** Detailed documents and instructions.
- **Example:** Images and examples of the final assembled product.
- **Circuitry:** Diagrams and files related to the electrical components.
