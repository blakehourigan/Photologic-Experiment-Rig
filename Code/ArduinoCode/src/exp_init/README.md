# Experiment Initialization Code

## The code in this directory is related to variables and functions that prepare the arduino for a new experiment.

### Primary functions include:

- Recieve experiment variables such as number of experiment trials and number of experiment stimuli. 
- Experiment variables allow the Arduino to safely receive the experiment valve schedule so that the required valves actuate during their assigned trial(s).
- Experiment variables also allow for safe receiving of valve opening time durations so that the Arduino knows how long to leave a valve open to get a desired 
amount of stimulant (generally 5 microliters).
