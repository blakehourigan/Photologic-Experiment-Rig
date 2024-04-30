#include <AccelStepper.h>
#include <avr/wdt.h>
#include "EEPROM_INTERFACE.h"
#include "Valve_control.h"
#include "serial_communication.h"
#include <EEPROM.h>
#include <vector>

#define dir_pin 53
#define step_pin 51

#define BAUD_RATE 115200

struct TimeStamp 
{
    String previous_command;
    int trial_number;
    unsigned long time_from_zero;
};

// Global variables - Schedule Transmission
int side_one_size = 0; 
int side_two_size = 0;
const int MAX_SCHEDULE_SIZE = 200;
int* SIDE_ONE_SCHEDULE;
int* SIDE_TWO_SCHEDULE;

// Global variables - Trials and licks
volatile bool lick_available = false;
int current_trial = 0;
int valve_number;
volatile int valve_side;

// Global variables - Program timing
unsigned long program_start_time; 
unsigned long duration;

// variables used in the loop function and related functions
String full_command;
String command;
bool prime_flag;
bool motor_running; 

// Global Timestamp vector (array) - Timestamp Collection and Transmission
std::vector<TimeStamp> timestamps;

AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);
EEPROM_INTERFACE eeprom_Interface;
valve_control valve_ctrl;
SerialCommunication serial_communication;



void add_to_array(int *array, int &size, int element) 
{
  if (size < MAX_SCHEDULE_SIZE) {
    array[size] = element;
    size++; // This now correctly increments the size.
  } else {
    Serial.println("Error: Array is full.");
  }
}

void send_valve_durations()
{
  unsigned long int values[16]; 

  char saved_duration_times[200];

  eeprom_Interface.read_values_from_EEPROM(values, eeprom_Interface.DATA_START_ADDRESS, 16);
  
  sprintf(saved_duration_times, "<Durations, S1, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, S2, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu>", 
          values[0], values[1], values[2], values[3], 
          values[4], values[5], values[6], values[7], 
          values[8], values[9], values[10], values[11], 
          values[12], values[13], values[14], values[15]);

  Serial.println(saved_duration_times);

  update_opening_times();
}

void test_volume(char number_of_valves)
{
  int num_valves = number_of_valves - '0';  // convert char to int

  for(int i=0; i < num_valves / 2; i++)
  {
    for(int j=0; j < 1000; j++)
    {
      valve_ctrl.lick_handler(0, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, current_trial, eeprom_Interface, i);
      valve_ctrl.lick_handler(1, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, current_trial, eeprom_Interface, i);
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

  send_valve_durations();
} 

bool is_integer(const String& str) {
    if (str.length() == 0) {
        return false; // Empty string is not an integer
    }
    
    int start = 0;
    if (str[0] == '-') {
        // Handle negative numbers
        if (str.length() == 1) {
            return false; // String is just "-", not an integer
        }
        start = 1; // Start checking from the next character
    }
    
    for (unsigned int i = start; i < str.length(); i++) {
        if (!isDigit(str[i])) {
            return false; // Found a non-digit character
        }
    }
    
    return true; // Passed all checks, it's an integer
}

void recieve_schedule(String full_command, int *SIDE_ONE_SCHEDULE, int *SIDE_TWO_SCHEDULE) 
{
    int currentIndex = 0;  // Tracks the current index for adding to arrays
    int side = 0;  // 0: not set, 1: side one, 2: side two
    String prev = "";
    int value = 0;
    // Start by splitting the command at every comma
    unsigned int from = 0;
    int to = full_command.indexOf(',', from);
    while (to != -1 || from < full_command.length()) 
    {
        String part = full_command.substring(from, to);

        if (part.equals("Side One") && prev.equals("S")) 
        {
            side = 1;  // Next numbers belong to side one
        } 
        else if (part.equals("Side Two") && prev.equals("-1"))
        {
            side = 2;  // Next numbers belong to side two
        } 
        else if (part.equals("end")) 
        {
            break;  // End of the entire command
        } 
        
        if (side != 0 && currentIndex < MAX_SCHEDULE_SIZE) 
        {
            // Convert part to integer and add to the correct array
            if(is_integer(part))
            {
            value = part.toInt();
            }
            else
            {
              prev = part;
              // Move to the next part
              from = to + 1;
              to = full_command.indexOf(',', from);
         
              if (to == -1 && from < full_command.length()) 
              {  // Handle the last part
              to = full_command.length();
              }
              continue;
            }
            if (side == 1 && value >= 0) 
            {
                add_to_array(SIDE_ONE_SCHEDULE, side_one_size, value);
            } else if (side == 2 && value >= 0) 
            {
                add_to_array(SIDE_TWO_SCHEDULE, side_two_size, value);
            }
        }
        prev = part;
        // Move to the next part
        from = to + 1;
        to = full_command.indexOf(',', from);

        if (to == -1 && from < full_command.length()) 
        {  // Handle the last part
            to = full_command.length();
        }
    }
    send_schedule_back(SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE);
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
}

void update_opening_times()
{
    const int num_values = 16;
    unsigned long int values[num_values];
    int valueIndex = 0;
    int startIndex = 0;
    int endIndex = 0;

    while (Serial.available() == 0) {}      // Wait until data is available

    String transmission = serial_communication.receive_transmission();

    // Parse the transmission string
    while ((endIndex = transmission.indexOf(',', startIndex)) != -1 && valueIndex < num_values) 
    {
      values[valueIndex++] = strtoul(transmission.substring(startIndex, endIndex).c_str(), NULL, 10);
      startIndex = endIndex + 1; // Move past the comma
    }

    // Capture the last value (assuming there's no trailing comma)
    if (valueIndex < num_values) {
      values[valueIndex] = strtoul(transmission.substring(startIndex).c_str(), NULL, 10);
    }
    
    eeprom_Interface.print_EEPROM_values();

    eeprom_Interface.write_values_to_EEPROM(values, eeprom_Interface.DATA_START_ADDRESS, 16);
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
}

void myISR() 
{
  valve_side = (PINH & (1 << PH5)) >> PH5;

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

  unsigned long int side_one_lick_durations[8]; 
  unsigned long int side_two_lick_durations[8];

  if (!eeprom_Interface.check_EEPROM_initialized())      // Check if EEPROM is initialized
  {
      for (int i = 0; i < 8; i++) 
      {
          side_one_lick_durations[i] = 24125; // Default value 24125
      }
      for (int i = 0; i < 8; i++) 
      {
          side_two_lick_durations[i] = 24125; // Default value 24125
      }

      eeprom_Interface.write_values_to_EEPROM(side_one_lick_durations, eeprom_Interface.DATA_START_ADDRESS, 8);
      eeprom_Interface.write_values_to_EEPROM(side_two_lick_durations, eeprom_Interface.DATA_START_ADDRESS + 8 * sizeof(long int), 8);
      eeprom_Interface.mark_EEPROM_initialized();
      Serial.println("EEPROM initialized with default values.");
  }
  else 
  {
      // Read the existing values from EEPROM
      eeprom_Interface.read_values_from_EEPROM(side_one_lick_durations, eeprom_Interface.DATA_START_ADDRESS, 8);
      eeprom_Interface.read_values_from_EEPROM(side_two_lick_durations, eeprom_Interface.DATA_START_ADDRESS + 8 * sizeof(long int), 8);
      //Serial.println("Values read from EEPROM.");
  }

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
}

void handle_motor_command(String command)
{
  const int STEPPER_UP_POSITION = 0;
  const int STEPPER_DOWN_POSITION = 6100;

  create_timestamp(command);

  if (command == "U")
  {
      noInterrupts();
      stepper.moveTo(STEPPER_UP_POSITION);
      interrupts();
  }
  else if (command == "D")
  {
      stepper.moveTo(STEPPER_DOWN_POSITION);
  }

  motor_running = true;
}


uint8_t create_portc_mask(int numberOfValves) 
{
  uint8_t mask = 0x00;
  for (int i = 0; i < numberOfValves; i++) 
  {
    mask |= (0x80 >> i); // Shift 0x80 (binary 1000 0000) right by 'i' positions
  }
  Serial.println(mask);
  return mask;
}

uint8_t create_porta_mask(int numberOfValves)
{
  uint8_t mask = 0x00;
  for (int i = 0; i < numberOfValves; i++) 
  {
    mask |= (0x01 << i); // Shift 0x80 (binary 1000 0000) right by 'i' positions
  }
  return mask;
} 


void loop() 
{
  if(lick_available) // if lick is available, send necessary data to the handler to open the corresponding valve on the schedule
  {
    valve_ctrl.lick_handler(valve_side, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, current_trial, eeprom_Interface);
    lick_available = false;
  }

  if (motor_running && stepper.distanceToGo() == 0) // check motor running first to avoid unneccessary calls to stepper.distanceToGo()
  {
    if(command.charAt(0) == 'U')
    {
      command = "FINISHED UP";
      create_timestamp(command);
      current_trial++; // Door is finished moving up, we are now on the next trial
    }
    else if(command.charAt(0) == 'D')
    {
      command = "FINSIHED DOWN";
      create_timestamp(command);
    }


    motor_running = false;
  }

  if (Serial.available() > 0) 
  {
    full_command = serial_communication.receive_transmission(); // Use the function to read the full command
    command = full_command[0]; // Assuming the format is <X>, where X is the command character
    prime_flag = 0;
    
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
      
      case 'F':
        prime_flag = 1; 
        valve_ctrl.prime_valves(prime_flag, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE, current_trial, eeprom_Interface);
        break;
      
      case 'O':
        int porta_value = 0;
        int portc_value = 0;
        Serial.println(full_command.c_str());
        if (sscanf(full_command.c_str(), "O,%d,%d", &porta_value, &portc_value) == 2) 
        {
          // If both numbers are successfully parsed, assign them to the ports
          PORTA = porta_value; // Assign the first number to PORTA
          PORTC = portc_value; // Assign the second number to PORTC
        } else 
        {
          // If parsing fails, log an error or handle the case appropriately
          Serial.println("Error parsing PORT values");
        }
        // Create a buffer to hold the formatted string
        char buffer[50]; // Ensure the buffer is large enough to hold the resulting string

        // Use sprintf to format the string into the buffer
        sprintf(buffer, "%d, %d", porta_value, portc_value);

        Serial.println(buffer);
        break;

      case 'S':
        recieve_schedule(full_command, SIDE_ONE_SCHEDULE, SIDE_TWO_SCHEDULE);
        break;
      
      case 'P':
        eeprom_Interface.print_EEPROM_values();
        break;
      
      case 'E':
        eeprom_Interface.markEEPROMUninitialized();
        break;
      
      case '0':   // mark t_0 time for the arduino side
        program_start_time = millis();
        create_timestamp(command);
        break;

      case '9':
        send_timestamps();
        break;
        
      default:
        break;
    }
  }
  stepper.run();
}