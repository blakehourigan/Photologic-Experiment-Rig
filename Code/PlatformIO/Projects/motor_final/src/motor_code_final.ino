#include <AccelStepper.h>
#include <avr/wdt.h>
#include <EEPROM.h>

#define SET_BIT(PORT, BIT) ((PORT) |= (1 << (BIT)))
#define CLEAR_BIT(PORT, BIT) ((PORT) &= ~(1 << (BIT)))
#define TOGGLE_BIT(PORT, BIT) ((PORT) ^= (1 << (BIT)))

#define dir_pin 53
#define step_pin 51

#define BAUD_RATE 115200

int current_trial = 0;

const int SIDE_ONE_SOLENOIDS[] = {PA0, PA1, PA2, PA3, PA4, PA5, PA6, PA7}; 
const int SIDE_TWO_SOLENOIDS[] = {PC7, PC6, PC5, PC4, PC3, PC2, PC1, PC0};

const int MAX_SCHEDULE_SIZE = 200; // Maximum size of the array
int SIDE_ONE_SCHEDULE[200];
int SIDE_TWO_SCHEDULE[200];

unsigned long start_time;
unsigned long end_time;
unsigned long duration;
unsigned long valve_open_time_d, valve_open_time_c, open_start, close_time;

int combined_value;

volatile int valve_side, valve_number;
volatile bool lick_available = false;
bool prime_flag;

int side_one_size = 0; // Keep track of the current number of elements
int side_two_size = 0;

AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);
const int MAX_SPEED = 5500; 
const int ACCELERATION = 5500;

#include "EEPROM_INTERFACE.h"

EEPROM_INTERFACE eeprom_Interface;

void clear_serial_buffer() 
{
  while (Serial.available() > 0) {
    Serial.read(); // Read and discard the incoming byte
  }
}

void add_to_array(int *array, int &size, int element) {
  if (size < MAX_SCHEDULE_SIZE) {
    array[size] = element;
    size++; // This now correctly increments the size.
  } else {
    Serial.println("Error: Array is full.");
  }
}

void toggle_solenoid(int side, int solenoid_pin) 
{
  if (side == 0)
  {
    TOGGLE_BIT(PORTA, solenoid_pin);
  }
  else if (side == 1)
  {
    TOGGLE_BIT(PORTC, solenoid_pin);
  }
}

void untoggle_solenoid(int side, int solenoid_pin) 
{
  if (side == 0)
  {
    CLEAR_BIT(PORTA, solenoid_pin);
  }
  else if (side == 1)
  {
    CLEAR_BIT(PORTC, solenoid_pin);
  }
}

void lick_handler(int valve_side, int valve_number = -1)
{
  const int * solenoids = (valve_side == 0) ? SIDE_ONE_SOLENOIDS : SIDE_TWO_SOLENOIDS; // if valve side is 0 (side 1), then choose side one solenoids, otherwise pick side two
  unsigned long int valve_duration = 0;
  
  noInterrupts();

  // choose starting address for eeprom values based on side
  int address = (valve_side == 0) ? eeprom_Interface.DATA_START_ADDRESS : eeprom_Interface.SIDE_TWO_DURATIONS_ADDRESS;

  if (valve_number == -1)  // if we do not give the function a valve, then use the schedule provided to find which one to use
  {
    valve_number = (valve_side == 0) ? SIDE_ONE_SCHEDULE[current_trial] : SIDE_TWO_SCHEDULE[current_trial];
  }
  
  eeprom_Interface.read_single_value_from_EEPROM(valve_duration, address, valve_number);

  int quotient = valve_duration / 10000; // delayMicroseconds only allows for values up to 16383, we use multiple instances of 
  // 10000 to avoid overflow

  int remaining_delay = valve_duration - (quotient * 10000);  

  toggle_solenoid(valve_side, solenoids[valve_number]);

  for (int i = 0; i < quotient; i++)
  {
    delayMicroseconds(10000);
  }

  delayMicroseconds(remaining_delay); // we add the remaining delay to the end of the loop to ensure the total duration is correct
  untoggle_solenoid(valve_side, solenoids[valve_number]);
  interrupts();
}

void prime_valves()
{
    for(int i = 0; i < 1000; i++)
    {
        if(prime_flag)
        {
          // Check if there's something on the serial line
          if (Serial.available() > 0) 
          {
              // Read the incoming byte:
              char incomingChar = Serial.read();

              // Check if the incoming byte is 'E'
              if (incomingChar == 'E') 
              {
                  prime_flag = 0; // Set prime_flag to zero to stop the priming
                  break; // Exit the for loop immediately
              }
          }

          // Prime valves as before
          // Prime all valves in both sides
          for (int side = 0; side <= 1; ++side) 
          {
              for (int valve_number = 0; valve_number < 4; ++valve_number) 
              {
                  lick_handler(side, valve_number);
              }
          }
          delay(100);
        }
        else
        {
            // If prime_flag is not set, break out of the loop early
            break;
        }
    }
}

void send_valve_durations()
{
  unsigned long int values[16]; 

  char saved_duration_times[200];

  eeprom_Interface.read_values_from_EEPROM(values, eeprom_Interface.DATA_START_ADDRESS, 16);
  
  sprintf(saved_duration_times, "<S1, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu, S2, %lu, %lu, %lu, %lu, %lu, %lu, %lu, %lu>", 
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
      lick_handler(0, i);
      lick_handler(1, i);
      delay(100);
    }
    clear_serial_buffer();
    delay(100);
    Serial.println("<Finished Pair>");

    while(true)
    {
      while (Serial.available() == 0) {}

      String received_transmission = receive_transmission();

      if(received_transmission == "continue")
      {
        break;
      }
    }
  }

  send_valve_durations();
} 

bool isInteger(const String& str) {
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

void recieve_schedule(String full_command) 
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
            if(isInteger(part))
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
    send_schedule_back();
}

void send_schedule_back() {
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


String receive_transmission()
{
    String message = "";
    char inChar;
    bool startDetected = false; // Flag to detect start of message
    // Keep reading characters until '>' is encountered
    while (true) {
        if (Serial.available() > 0) {
            inChar = Serial.read();
            // Check for the end of the message
            if (inChar == '>') {
                break; // End of message, exit the loop
            }
            // Skip adding to message until start character '<' is found
            if (inChar == '<') {
                startDetected = true; // Mark start detected
                continue; // Skip adding the '<' character
            }
            if (startDetected) {
                message += inChar; // Add the character to the message string only after '<' is detected
            }
        }
    }
    return message; // Return the complete message read from Serial, excluding the starting character '<'
}

void update_opening_times()
{
    const int num_values = 16;
    unsigned long int values[num_values];
    int valueIndex = 0;
    int startIndex = 0;
    int endIndex = 0;

    while (Serial.available() == 0) {}      // Wait until data is available

    String transmission = receive_transmission();

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




void myISR() 
{
  valve_side = (PINH & (1 << PH5)) >> PH5;

  lick_available = true;

}

void setup() 
{
  stepper.setMaxSpeed(MAX_SPEED);
  stepper.setAcceleration(ACCELERATION);
  Serial.begin(BAUD_RATE);

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

  for(unsigned int i = 0; i < sizeof(inputPins)/sizeof(inputPins[0]); i++) 
  {
      pinMode(inputPins[i], INPUT_PULLUP);
  }

  attachInterrupt(0, myISR, RISING); // attach interrupt on pin 2 to know when licks are detected

}


void loop() 
{
  if(lick_available)
  {
    lick_handler(valve_side);
    lick_available = false;
  }

  if (Serial.available() > 0) 
  {
    String fullCommand = receive_transmission(); // Use the function to read the full command
    char command = fullCommand[0]; // Assuming the format is <X>, where X is the command character

    switch (command) 
    {
      case 'U':
        stepper.moveTo(0);
        break;
      case 'D':
        stepper.moveTo(6400);
        break;
      case 'R':
        wdt_enable(WDTO_1S);
        break;
      case 'W':
        Serial.println("MOTOR");
        break;
      case 'T':
        command = fullCommand[2];
        test_volume(command);
        break;
      case 'F':
        prime_flag = 1;
        prime_valves();
        break;
      case 'O':
        for(int i = 0; i < 8; i++)
        {
          PORTA |= (255); // open all valves on side 1
          PORTC |= (255); // open all valves on side 2
        } 
        break;
      case 'C':    
        for(int i = 0; i < 8; i++)
        {
          PORTA &= ~(255); // close all valves on side 1
          PORTC &= ~(255); // close all valves on side 2
        }
        break;
      case 'I':
        current_trial++;
        break;
      case 'S':
      {
        recieve_schedule(fullCommand);
        break;
      }
      case 'P':
      {
        eeprom_Interface.print_EEPROM_values();
        break;
      }
      case 'E':
      {
        eeprom_Interface.markEEPROMUninitialized();
        break;
      }
      default:
        break;
    }
  }
  stepper.run();
}