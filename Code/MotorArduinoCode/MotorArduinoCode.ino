#include <AccelStepper.h>
#include <avr/wdt.h>
#include "./src/valve_control/valve_control.h"
#include "./src/exp_init/exp_init.h"
#include <Vector.h>

#define dir_pin 53
#define step_pin 51
#define BAUD_RATE 115200

// variable is volatile because its value is checked in an interrupt
// service routine
volatile bool lick_available = false;

// since we support up to 320 trials, 
// we need more than 2^8 = 255 we use 
// 16 bit int which provides vals up to 2^16 -1 = 65535
uint16_t current_trial = 0;

// only holds 0 or 1
volatile uint8_t valve_side = 0;

unsigned long program_start_time = 0; 

// used to calculate which valve to select on side two.
const uint8_t TOTAL_VALVES= 8;

// door stepper motor constants
const int STEPPER_UP_POSITION = 0;
const int STEPPER_DOWN_POSITION = 6000;
const int MAX_SPEED = 5500; 
const int ACCELERATION = 5500;
bool motor_running = false; 
bool experiment_started = false;

String previous_command;

AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);
valve_control valve_ctrl;

void handle_lick(){
  volatile uint8_t *PORT;
  
  uint8_t valve_num = 0;
  long int duration = 0;

  if (valve_side == 0){
    valve_num = side_one_sched_vec.at(current_trial);
    duration = side_one_dur_vec.at(valve_num);
    PORT = &PORTA;

  }else{
    // port is already calculated previously, however since ports are split between 
    // PORTA for side1 and PORTC for side 2 we must fix the pin num if side 2. 
    // subtract valves / 2 from valve num -> valve num 5 becomes 5 - (8/2) = 1
    // first pin on PORTC is actuated. The only thing that would change this calculation is 
    // if total number of valves changed.
    valve_num = side_two_sched_vec.at(current_trial);

    valve_num = valve_num - (TOTAL_VALVES / 2);
    duration = side_two_dur_vec.at(valve_num);
    PORT = &PORTC;
  }

  valve_ctrl.lick_handler(valve_num, duration, PORT);
  lick_available = false;

}

void complete_motor_movement(String previous_command){
  /* 
  This function is called when the door finishes a movement operation. It takes the previous command as 
  a parameter and tells the python controller that a movement has completed and which type of movement 
  that was, so that we can mark these movements down in the lick dataframe. If the movement was up, 
  that means a trial just ended and we can increment to the next trial.
  */
  String command_description = "\0";

  if (previous_command.equals("UP")){
    //// Door is finished moving up, we are now on the next trial
    current_trial++; 
    Serial.println("MOTOR MOVED UP");
  }
  else if(previous_command.equals("DOWN")){
    Serial.println("MOTOR MOVED DOWN");
  }
  motor_running = false;
}

void myISR() 
{
  valve_side = (PINH & (1 << PH5)) >> PH5;

  lick_available = true;
}

void setup() 
{
  Serial.begin(BAUD_RATE);

  stepper.setMaxSpeed(MAX_SPEED);
  stepper.setAcceleration(ACCELERATION);

  // Set pins 22-29 as outputs (side one valves)
  DDRA |= (255); 
  // Set pins 30-37 as outputs (side two valves)
  DDRC |= (255); 

  int inputPins[] = {2, 8, 9, 10, 11, 12};

  for(unsigned int i = 0; i < sizeof(inputPins) / sizeof(inputPins[0]); i++) 
  {
    pinMode(inputPins[i], INPUT_PULLUP);
  }

  // attach interrupt on pin 2 to know when licks are detected
  attachInterrupt(0, myISR, RISING); 
}

void loop() 
{
  String command = "\0";
  // if lick is available, send necessary data to the handler to open the corresponding valve on the schedule
  if(lick_available && experiment_started) {
    //Serial.print("Lick detected on side: ");
    //Serial.println(valve_side);
    handle_lick();
  }

  // check motor running first to avoid unneccessary calls to stepper.distanceToGo()
  if (motor_running && stepper.distanceToGo() == 0) {
    complete_motor_movement(previous_command);
  }

  if (Serial.available() > 0) {
    // read until the newline char 
    command = Serial.readStringUntil('\n');
  }
  // only process command cases if one has been recieved from the controller
  if (!command.equals("\0")){
    // tell door motor to move up
    if (command.equals("UP")) {
      noInterrupts();
      stepper.moveTo(STEPPER_UP_POSITION);
      interrupts();
      //Serial.println("Stepper moving up.");
      previous_command = command;
      motor_running = true;
    }
    // tell door motor to move down
    else if (command.equals("DOWN")){
      stepper.moveTo(STEPPER_DOWN_POSITION);
      //Serial.println("Stepper moving down.");
      previous_command = command;
      motor_running = true;
    }
    // reset the board
    else if (command.equals("RESET")){
      wdt_enable(WDTO_1S);
    }

    else if (command.equals("WHO ARE YOU")){
      Serial.println("MOTOR");
    }
    else if (command.equals("TEST VOL")){
      //test_volume(full_command[2]);
    }
    else if (command.equals("OPEN SPEC")){
      // int porta_value = 0;
      // int portc_value = 0;
      // if (sscanf(full_command.c_str(), "O,%d,%d", &porta_value, &portc_value) == 2) 
      // {
      //   // If both numbers are successfully parsed, assign them to the ports
      //   // Assign the first number to PORTA
      //   PORTA = porta_value; 
      //   // Assign the second number to PORTC
      //   PORTC = portc_value; 
      //   Serial.print("Set PORTA to: "); Serial.println(porta_value);
      //   Serial.print("Set PORTC to: "); Serial.println(portc_value);
      // } else 
      // {
      //   // If parsing fails, log an error or handle the case appropriately
      //   Serial.println("Error parsing PORT values");
      // }
    }
    // mark t=0 time for the arduino side
    else if (command.equals("T=0")){
      program_start_time = millis();

      experiment_started = true;
    }
    // receive valve durations from the python controller
    else if (command.equals("REC DURATIONS")){
      receive_durations();
    }
    // handle recieving program schedule
    else if (command.equals("REC SCHED")){
      receive_schedules();
    }
    // handle recieving program variables (num_stim, num_trials)
    else if (command.equals("REC VAR")){
      receive_exp_variables();
    }
    else if (command.equals("VER SCHED")){
      schedule_verification();
    }
    else if (command.equals("VER DURATIONS")){
      durations_verification();
    }
    else {
      Serial.print("Unknown command received: ");
      if (command == "\0"){
        Serial.println("null command");
      }
      Serial.println(command);
    }
  }
  stepper.run();
}

