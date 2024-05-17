#include <ArduinoJson.h>
#include <AccelStepper.h>
#include <avr/wdt.h>
#include "Valve_control.h"
#include "serial_communication.h"
#include <vector>

#define dir_pin 53
#define step_pin 51
#define BAUD_RATE 115200

struct TimeStamp {
    String previous_command;
    int trial_number;
    unsigned long time_from_zero;
};

// Define buffer size
const size_t bufferSize = 512; // Adjust buffer size as needed
char jsonBuffer[bufferSize];

// Define other global variables as needed
int side_one_size = 0; 
int side_two_size = 0;
const int VALVES_SIDE_ONE = 8;
const int VALVES_SIDE_TWO = 8;
const int MAX_SCHEDULE_SIZE = 200;
int* SIDE_ONE_SCHEDULE;
int* SIDE_TWO_SCHEDULE;
unsigned long *side_one_durations;
unsigned long *side_two_durations;
volatile bool lick_available = false;
int current_trial = 0;
int valve_number;
volatile int valve_side;
unsigned long program_start_time; 
String full_command;
String command;
bool prime_flag;
bool motor_running; 
bool connected = false;
bool experiment_started = false;
std::vector<TimeStamp> timestamps;
AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);
valve_control valve_ctrl;
SerialCommunication serial_communication;

void add_to_array(int *array, int &size, int element) 
{
  if (size < MAX_SCHEDULE_SIZE) {
    array[size] = element;
    size++; // This now correctly increments the size.
    Serial.print("Added to array: "); Serial.println(element);
  } else {
    Serial.println("Error: Array is full.");
  }
}

void receive_data_dictionary(const char* jsonData) {
    DynamicJsonDocument doc(bufferSize);
    DeserializationError error = deserializeJson(doc, jsonData);
    if (error) {
        Serial.print("deserializeJson() failed: ");
        Serial.println(error.c_str());
        return;
    }

    // Extract the data from the JSON object
    JsonArray side_one_schedule = doc["side_one_schedule"];
    JsonArray side_two_schedule = doc["side_two_schedule"];
    int current_trial = doc["current_trial"];
    JsonArray valve_durations_side_one = doc["valve_durations_side_one"];
    JsonArray valve_durations_side_two = doc["valve_durations_side_two"];

    // Update the global variables
    side_one_size = side_one_schedule.size();
    side_two_size = side_two_schedule.size();

    // Resize and populate the SIDE_ONE_SCHEDULE array
    if (SIDE_ONE_SCHEDULE) delete[] SIDE_ONE_SCHEDULE;
    SIDE_ONE_SCHEDULE = new int[side_one_size];
    for (int i = 0; i < side_one_size; i++) {
        SIDE_ONE_SCHEDULE[i] = side_one_schedule[i].as<int>();
    }

    // Resize and populate the SIDE_TWO_SCHEDULE array
    if (SIDE_TWO_SCHEDULE) delete[] SIDE_TWO_SCHEDULE;
    SIDE_TWO_SCHEDULE = new int[side_two_size];
    for (int i = 0; i < side_two_size; i++) {
        SIDE_TWO_SCHEDULE[i] = side_two_schedule[i].as<int>();
    }

    // Resize and populate the SIDE_ONE_SCHEDULE array
    if (side_one_durations) delete[] side_one_durations;
    side_one_durations = new unsigned long[VALVES_SIDE_ONE];
    for (int i = 0; i < VALVES_SIDE_ONE; i++) {
        side_one_durations[i] = valve_durations_side_one[i].as<int>();
    }

    // Resize and populate the SIDE_TWO_SCHEDULE array
    if (side_two_durations) delete[] side_two_durations;
    side_two_durations = new unsigned long[VALVES_SIDE_TWO];
    for (int i = 0; i < VALVES_SIDE_TWO; i++) {
        side_two_durations[i] = valve_durations_side_two[i].as<int>();
    }


    // Update the current trial
    current_trial = current_trial;

    // Print side_one_schedule
    Serial.println("side_one_schedule:");
    for (JsonVariant value : side_one_schedule) {
      Serial.println(value.as<int>());
    }

    // Print side_two_schedule
    Serial.println("side_two_schedule:");
    for (JsonVariant value : side_two_schedule) {
      Serial.println(value.as<int>());
    }

    // Print current_trial
    Serial.print("current_trial: ");
    Serial.println(current_trial);

    // Print valve_durations
    Serial.println("valve_durations_side_one:");
    for (JsonVariant value : valve_durations_side_one) {
      Serial.println(value.as<int>());
    }
    Serial.println("valve_durations_side_two:");
    for (JsonVariant value : valve_durations_side_one) {
      Serial.println(value.as<int>());
    }


    Serial.println("Data dictionary received and processed.");
}

void test_volume(char number_of_valves)
{
  int num_valves = number_of_valves - '0';  // convert char to int
  Serial.print("Testing volume with "); Serial.print(num_valves); Serial.println(" valves.");

  for(int i=0; i < num_valves / 2; i++)
  {
    Serial.print("Testing valve pair: "); Serial.println(i+1);
    for(int j=0; j < 1000; j++)
    {
      Serial.print("testing...");
      valve_ctrl.lick_handler(0, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, side_one_durations, side_two_durations, current_trial, true, i);
      valve_ctrl.lick_handler(1, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, side_one_durations, side_two_durations ,current_trial, true, i);
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
} 

void send_schedule_back(int *SIDE_ONE_SCHEDULE, int *SIDE_TWO_SCHEDULE) {
  String message = "SCHEDULE VERIFICATION";

  for (int i = 0; i < side_one_size; i++) {
    message += SIDE_ONE_SCHEDULE[i];
    message += ',';
  }

  for (int i = 0; i < side_two_size; i++) {
    message += SIDE_TWO_SCHEDULE[i];
    if (i < side_two_size - 1) {
      message += ','; // Add comma separator between items
    }
  }

  Serial.println(message); // Send the entire schedule in one line
  Serial.println("Schedule sent back for verification.");
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
  const int MAX_SPEED = 5500; 
  const int ACCELERATION = 5500;

  stepper.setMaxSpeed(MAX_SPEED);
  stepper.setAcceleration(ACCELERATION);
  Serial.begin(BAUD_RATE);

  SIDE_ONE_SCHEDULE = new int[MAX_SCHEDULE_SIZE];
  SIDE_TWO_SCHEDULE = new int[MAX_SCHEDULE_SIZE];

  DDRA |= (255); // Set pins 22-29 as outputs
  DDRC |= (255); // Set pins 30-37 as outputs 
  
  int inputPins[] = {2, 8, 9, 10, 11, 12};

  for(unsigned int i = 0; i < sizeof(inputPins) / sizeof(inputPins[0]); i++) 
  {
      pinMode(inputPins[i], INPUT_PULLUP);
  }

  attachInterrupt(0, myISR, RISING); // attach interrupt on pin 2 to know when licks are detected
}

void create_timestamp(String command)
{
  TimeStamp timestamp;

  timestamp.previous_command = command; // Assuming 'command' holds the previous command
  timestamp.trial_number = current_trial + 1;
  timestamp.time_from_zero = millis() - program_start_time;

  timestamps.push_back(timestamp);
  Serial.print("Timestamp created for command: "); Serial.println(command);
}

void handle_motor_command(String command)
{
  const int STEPPER_UP_POSITION = 0;
  const int STEPPER_DOWN_POSITION = 6000;

  create_timestamp(command);

  if (command == "U")
  {
      noInterrupts();
      stepper.moveTo(STEPPER_UP_POSITION);
      interrupts();
      Serial.println("Stepper moving up.");
  }
  else if (command == "D")
  {
      stepper.moveTo(STEPPER_DOWN_POSITION);
      Serial.println("Stepper moving down.");
  }

  motor_running = true;
}

void loop() 
{
  if(lick_available && experiment_started) // if lick is available, send necessary data to the handler to open the corresponding valve on the schedule
  {
    valve_ctrl.lick_handler(valve_side, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, side_one_durations,side_two_durations ,current_trial, false, -1);
    lick_available = false;
    Serial.println("Handled lick event.");
  }

  if (motor_running && stepper.distanceToGo() == 0) // check motor running first to avoid unneccessary calls to stepper.distanceToGo()
  {
    if(command.charAt(0) == 'U')
    {
      command = "FINISHED UP";
      create_timestamp(command);
      current_trial++; // Door is finished moving up, we are now on the next trial
      Serial.println("Motor finished moving up.");
    }
    else if(command.charAt(0) == 'D')
    {
      command = "FINISHED DOWN";
      create_timestamp(command);
      Serial.println("Motor finished moving down.");
    }

    motor_running = false;
  }

  if (Serial.available() > 0) 
  {
    full_command = serial_communication.receive_transmission(); // Use the function to read the full command
    command = full_command[0]; // Assuming the format is <X>, where X is the command character
    prime_flag = 0;
    if(connected){
    Serial.print("Received command: "); Serial.println(full_command);
    }
    
    switch (command.charAt(0)) 
    {
      case 'U':
      case 'D':
        handle_motor_command(command);
        break;

      case 'R':
        delete[] SIDE_ONE_SCHEDULE;
        delete[] SIDE_TWO_SCHEDULE;
        wdt_enable(WDTO_1S);
        break;
      
      case 'W':
        Serial.println("MOTOR");
        break;
      
      case 'T':
        command = full_command[2];
        test_volume(command.charAt(0));
        break;
      case 'O':
      {
        int porta_value = 0;
        int portc_value = 0;
        if (sscanf(full_command.c_str(), "O,%d,%d", &porta_value, &portc_value) == 2) 
        {
          // If both numbers are successfully parsed, assign them to the ports
          PORTA = porta_value; // Assign the first number to PORTA
          PORTC = portc_value; // Assign the second number to PORTC
          Serial.print("Set PORTA to: "); Serial.println(porta_value);
          Serial.print("Set PORTC to: "); Serial.println(portc_value);
        } else 
        {
          // If parsing fails, log an error or handle the case appropriately
          Serial.println("Error parsing PORT values");
        }
        break;
      }
      case '0':   // mark t_0 time for the arduino side
        program_start_time = millis();
        experiment_started = true;
        create_timestamp(command);
        Serial.println("Program start time set.");
        break;

      case '9':
        send_timestamps();
        break;
      case 'A': // New command to receive the data dictionary
        if (full_command.startsWith("A,")) {
            String jsonData = full_command.substring(2);
            receive_data_dictionary(jsonData.c_str());
        }
        break;
      default:
        Serial.println("Unknown command received.");
        break;
    }
  }
  stepper.run();
}
