# Source Code Directory Structure

This directory contains all source code for the program, as well as all configuration dependencies that are needed to run the program. These configuration files, along with other program 'assets' such as the program rat icon are located here. 

## MVC Architechture
An attempt was made to follow the Model-View-Controller architechture as closely as possible. In this model, 
the controller files manage interation between different components of the program. For example, models (data) 
should not interact directly with any view (GUI windows). These interations are instead managed through controller 
files. Somewhat confusingly then, the main 'controller' in this program is not in the controller directory but is 
instead called 'app_logic' and resides in the root of the /src directory. I felt this made the most sense as 
it is the source or the root of all other actions and files. As such it is placed at the root.

## Models
The models are the first classes instantiated when the program starts because all other classes require some access 
to the data that is held here. Global program variables that are passed around to various classes during 
program and experiment execution are stored here. Here you'll find data specific to different parts of the program, 
including 'experiment_process_data.py' where data regarding experiment specific data such as schedule generation, 
maximum runtime calculations, program schedule dataframe data (trial, licks per port, stimuli on a given trial, etc),
etc.

Continuing along these lines you'll find data specific to the arduino, detailed data on program events (door movements, lick times), and stimuli specific data in their respective directories.

## Views 
Finally, you'll find the views directory. As you might imagine, this directory contains all code involving the 
interactive Graphical User Interface (GUI). Every peice of code that defines something that a user interacts with 
or looks at is defined here. As before, the files have descriptive names that reveal which task they perform. 

## Controllers
This directory contains controllers other than the primary controller. Which at the time of writing contains only
the Arduino controller files. This handles interactions between Aduino specific data (models/arduino_data.py) and
Arduino specific actions. The primary action handled here is communication between the Arduino board and this 
program.

I hope that this structure proves easy to understand and navigate. I thought a lot about, and worked hard to ensure
that this would be the case.

-BH
