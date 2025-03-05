#include <ArduinoJson.h>
#include <AccelStepper.h>
#include <avr/wdt.h>
#include "valve_control.h"
#include "serial_communication.h"
#include <Vector.h>

#define dir_pin 53
#define step_pin 51
#define BAUD_RATE 115200

struct TimeStamp {
    String previous_command;
    int trial_number;
    unsigned long time_from_zero;
};

// maximum # of valves per side 
// so that we know how many durations we need
const int VALVES_PER_SIDE = 8;

unsigned long side_one_durations[VALVES_PER_SIDE];
unsigned long side_two_durations[VALVES_PER_SIDE];
Vector<unsigned long> side_one_dur_vec = side_one_durations;
Vector<unsigned long> side_two_dur_vec= side_two_durations;

const int MAX_SCHEDULE_SIZE = 320;
const int MAX_DURATION_SIZE = 320;

uint8_t side_one_schedule[MAX_SCHEDULE_SIZE];
uint8_t side_two_schedule[MAX_SCHEDULE_SIZE];
Vector<uint8_t> side_one_sched_vec = side_one_schedule;
Vector<uint8_t> side_two_sched_vec =  side_two_schedule;

volatile bool lick_available = false;

// experiment related variables
uint8_t num_stimuli = 0;
uint8_t num_trials = 0;
int current_trial = 0;

int valve_number;
volatile int valve_side;

unsigned long program_start_time; 


// door stepper motor constants
const int STEPPER_UP_POSITION = 0;
const int STEPPER_DOWN_POSITION = 6000;
const int MAX_SPEED = 5500; 
const int ACCELERATION = 5500;
bool motor_running = false; 
bool experiment_started = false;

Vector<TimeStamp> timestamps;
AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);
valve_control valve_ctrl;
SerialCommunication serial_communication;

void receive_exp_variables(){
  /* function to recieve program variables such as num_stimuli
   * and num_trials.
   * 
   * num stimuli will be sent in the first byte, while num_trials 
   * will follow behind
   */
   // if we have 2 bytes available, read number_stimuli in
   num_stimuli = 0;
   num_trials = 0;
   // wait until we know that both bytes have arrived sequentially.
   while(Serial.available() < 2){
   } 
   // once they are read one byte at a time into repective variables
   num_stimuli = Serial.read();

   num_trials = Serial.read();

}


void receive_schedules(){
  //JsonArray side_one_schedule = doc["side_one_schedule"];
  //JsonArray side_two_schedule = doc["side_two_schedule"];
  // Resize and populate the SIDE_ONE_SCHEDULE array

  // loop until we've read all bytes
  int elements_processed = 0;
  // max elements per side is num_trials - 1 due to zero indexing
  int valve = 0;
  // side starts at 1
  int side = 1;

  while(1){
    // if we have any serial bytes available, read one byte in and 
    // say that this byte represents which valve to select for this trial
    if(Serial.available() > 0){
      valve = Serial.read();
      elements_processed++;

      if (side == 1){
        side_one_sched_vec.push_back(valve);
      }else if(side == 2){
        side_two_sched_vec.push_back(valve);
      }
      if (elements_processed == num_trials){
        if (side == 1){
          elements_processed = 0;
          side = 2;
        } else{
          break;
        }
      }
    }
  }
}


//void receive_durations() {
//   
//
//    
//    int cur_trial = doc["current_trial"];
//    JsonArray valve_durations_side_one = doc["valve_durations_side_one"];
//    JsonArray valve_durations_side_two = doc["valve_durations_side_two"];
//
//    // Update the global variables
//    side_one_size = side_one_schedule.size();
//    side_two_size = side_two_schedule.size();
//
//    
//    // Resize and populate the SIDE_ONE_SCHEDULE array
//    side_one_durations = new unsigned long[VALVES_SIDE_ONE];
//    
//    for (int i = 0; i < VALVES_SIDE_ONE; i++) {
//        side_one_durations[i] = valve_durations_side_one[i].as<int>();
//    }
//
//    // create new array for side_two_durations
//    side_two_durations = new unsigned long[VALVES_SIDE_TWO];
//    
//    for (int i = 0; i < VALVES_SIDE_TWO; i++) {
//        side_two_durations[i] = valve_durations_side_two[i].as<int>();
//    }
//
//
//    // Update the current trial
//    current_trial = cur_trial;
//
//    // Print side_one_schedule
//    Serial.println("side_one_schedule:");
//    for (JsonVariant value : side_one_schedule) {
//      Serial.println(value.as<int>());
//    }
//
//    // Print side_two_schedule
//    Serial.println("side_two_schedule:");
//    for (JsonVariant value : side_two_schedule) {
//      Serial.println(value.as<int>());
//    }
//
//    // Print current_trial
//    Serial.print("current_trial: ");
//    Serial.println(current_trial);
//
//    // Print valve_durations
//    Serial.println("valve_durations_side_one:");
//    for (JsonVariant value : valve_durations_side_one) {
//      Serial.println(value.as<int>());
//    }
//    Serial.println("valve_durations_side_two:");
//    for (JsonVariant value : valve_durations_side_one) {
//      Serial.println(value.as<int>());
//    }
//
//
//    Serial.println("Data dictionary received and processed.");
//}

void test_volume(char number_of_valves)
{
  int num_valves = number_of_valves - '0';  // convert char to int
  Serial.print("Testing volume with "); Serial.print(num_valves); Serial.println(" valves.");

  for(int i=0; i < num_valves / 2; i++) // i is the current valve number on either side
  {
    Serial.print("Testing valve pair: "); Serial.println(i+1);
    for(int j=0; j < 1000; j++)
    {
      //valve_ctrl.lick_handler(0, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, side_one_durations, side_two_durations, current_trial, true, i);
      //valve_ctrl.lick_handler(1, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, side_one_durations, side_two_durations ,current_trial, true, i);
      delay(100);
    }
    serial_communication.clear_serial_buffer();
    delay(100);
    Serial.println("<Finished Pair>");

    while(true)
    {
      while (Serial.available() == 0) {}

      String received_transmission = serial_communication.receive_transmission();

      if(received_transmission == "continue")
      {
        break;
      }
    }
  }
  Serial.println("Testing Complete");


}

void schedule_verification() {
  // echo recieved schedules to python controller, so that it can verify that 
  // we received them correctly
  for (int i = 0; i < side_one_sched_vec.size(); i++){
    Serial.print(side_one_sched_vec.at(i));
  }
  //Serial.println();

  for (int i = 0; i < side_two_sched_vec.size(); i++){
    Serial.print(side_two_sched_vec.at(i));
  }
  Serial.println();

  //Serial.println("Schedule sent back for verification.");
}

void send_timestamps() {
  String timestampsData = "";
  timestampsData += "Time Stamp Data";
  for (const auto& timestamp : timestamps) {
    timestampsData += "<";
    timestampsData += timestamp.previous_command;
    timestampsData += ",";
    timestampsData += String(timestamp.trial_number);
    timestampsData += ",";
    timestampsData += String(timestamp.time_from_zero);
    timestampsData += ">";
  }

  Serial.println(timestampsData);
  Serial.println("Sent timestamps data.");
}

void myISR() 
{
  valve_side = (PINH & (1 << PH5)) >> PH5;
  Serial.print("Lick detected on side: "); Serial.println(valve_side);

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

void create_timestamp(String command)
{
  TimeStamp timestamp;

  // Assuming 'command' holds the previous command
  timestamp.previous_command = command; 
  timestamp.trial_number = current_trial + 1;
  timestamp.time_from_zero = millis() - program_start_time;

  timestamps.push_back(timestamp);
  Serial.print("Timestamp created for command: "); Serial.println(command);
}


void handle_lick(){
  volatile uint8_t *PORT;
  int valve_num = 0;
  long int duration = 0;

  if (valve_side == 0){
    valve_num = side_one_sched_vec.at(current_trial);
    duration = side_one_dur_vec.at(current_trial);
    PORT = &PORTA;

  }else{
    valve_num = side_two_sched_vec.at(current_trial);
    duration = side_two_dur_vec.at(current_trial);
    PORT = &PORTC;

    // port is already calculated previously, however since ports are split between 
    // PORTA for side1 and PORTC for side 2 we must fix the pin num if side 2. 
    // subtract num_stim / 2 from valve num -> valve num 5 becomes 5 - (8/2) = 1
    // first pin on PORTC is actuated
    valve_num = valve_num - (num_stimuli / 2);

  }

  valve_ctrl.lick_handler(valve_num, duration, PORT);
  lick_available = false;
  Serial.println("Handled lick event.");

}

void complete_motor_movement(String command){
  String command_description = "\0";

    if (command.equals("UP")){
      //command = "FINISHED UP";
      //create_timestamp(command);

      //// Door is finished moving up, we are now on the next trial
      //current_trial++; 
      //Serial.println("Motor finished moving up.");
    }
    else if(command.equals("DOWN")){
      //command = "FINISHED DOWN";
      //create_timestamp(command);

      //Serial.println("Motor finished moving down.");
    }
    motor_running = false;
}


void loop() 
{
  String command = "\0";
  // if lick is available, send necessary data to the handler to open the corresponding valve on the schedule
  if(lick_available && experiment_started) {
    handle_lick();
  }

  // check motor running first to avoid unneccessary calls to stepper.distanceToGo()
  if (motor_running && stepper.distanceToGo() == 0) {
    // THIS NEEDS TO BE FIXED.... IT WILL GET NULL EVERY TIME RIGHT NOW
    complete_motor_movement(command);
  }

  if (Serial.available() > 0) {
    // read until the newline char 
    command = Serial.readStringUntil('\n');
  }

  if (!command.equals("\0")){


    // tell door motor to move up
    if (command.equals("UP")) {
      noInterrupts();
      stepper.moveTo(STEPPER_UP_POSITION);
      interrupts();
      Serial.println("Stepper moving up.");
      motor_running = true;
    }
    // tell door motor to move down
    else if (command.equals("DOWN")){
      stepper.moveTo(STEPPER_DOWN_POSITION);
      Serial.println("Stepper moving down.");
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
      //create_timestamp(command);
      Serial.println("Program start time set.");
    }
    // send door motor up/down timestamps to the python controller
    else if (command.equals("SEND TIMESTAMPS")){
      send_timestamps();
    }
    // receive valve durations from the python controller
    else if (command.equals("REC DURATIONS")){
      //receive_durations();
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
    else {
      Serial.print("Unknown command received: ");
      if (command == "\0"){
        Serial.println("null");
      }
      Serial.println(command);
    }
  }
  stepper.run();
}

