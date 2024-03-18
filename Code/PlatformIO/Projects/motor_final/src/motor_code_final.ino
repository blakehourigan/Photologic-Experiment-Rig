#include <AccelStepper.h>
#include <avr/wdt.h>
#include <EEPROM.h>

#define SET_BIT(PORT, BIT) ((PORT) |= (1 << (BIT)))
#define CLEAR_BIT(PORT, BIT) ((PORT) &= ~(1 << (BIT)))
#define TOGGLE_BIT(PORT, BIT) ((PORT) ^= (1 << (BIT)))

#define dir_pin 53
#define step_pin 51

int current_trial = 0;

const int SIDE_ONE_SOLENOIDS[] = {PA0, PA1, PA2, PA3, PA4, PA5, PA6, PA7}; 
const int SIDE_TWO_SOLENOIDS[] = {PC7, PC6, PC5, PC4, PC3, PC2, PC1, PC0};

int SIDE_ONE_SCHEDULE[50];
int SIDE_TWO_SCHEDULE[50];

unsigned long start_time;
unsigned long end_time;
unsigned long duration;
unsigned long valve_open_time_d, valve_open_time_c, open_start, close_time;

int combined_value;

int valve_side, valve_number;
bool lick_available = false;

const int FLAG_ADDRESS = 0;
const byte INITIALIZED_FLAG = 0xA5;
const int DATA_START_ADDRESS = 1; // Start after the flag

long int side_one_lick_durations[8]; 
long int side_two_lick_durations[8];

const int MAX_SIZE = 50; // Maximum size of the array
int side_one_size = 0; // Keep track of the current number of elements
int side_two_size = 0;

AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);

void clear_serial_buffer() 
{
  while (Serial.available() > 0) {
    Serial.read(); // Read and discard the incoming byte
  }
}

bool checkEEPROMInitialized() 
{
    byte flag;
    EEPROM.get(FLAG_ADDRESS, flag);
    return (flag == INITIALIZED_FLAG);
}

void markEEPROMInitialized() 
{
    EEPROM.update(FLAG_ADDRESS, INITIALIZED_FLAG);
}

// Function to write default or new values to EEPROM
void writeValuesToEEPROM(long int values[], int startAddress, int numValues) 
{
    for (int i = 0; i < numValues; i++) {
        EEPROM.put(startAddress + i * sizeof(long int), values[i]);
    }
}

// Function to read values from EEPROM
void readValuesFromEEPROM(long int values[], int startAddress, int numValues) 
{
    for (int i = 0; i < numValues; i++) 
    {
        EEPROM.get(startAddress + i * sizeof(long int), values[i]);
    }
}


void addToArray(int *array, int &size, int element) {
  if (size < MAX_SIZE) {
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
  const int * solenoids;
  long int duration = 0;

  noInterrupts();


  if (valve_number != -1) 
  {
    // Use the provided valve number
    if (valve_side == 0) 
    {
      duration = side_one_lick_durations[valve_number];
      solenoids = SIDE_ONE_SOLENOIDS;
    } else if (valve_side == 1) 
    {
      duration = side_two_lick_durations[valve_number];
      solenoids = SIDE_TWO_SOLENOIDS;
    } else 
    {
      Serial.println("Invalid solenoid value");
      return;
    }
  }
  else
  {
    if(valve_side == 0)
    {
      duration = side_one_lick_durations[valve_number];
      solenoids = SIDE_ONE_SOLENOIDS;
      valve_number = SIDE_ONE_SCHEDULE[current_trial];
    }
    else if(valve_side == 1)
    {
      duration = side_two_lick_durations[valve_number];
      solenoids = SIDE_TWO_SOLENOIDS;
      valve_number = SIDE_TWO_SCHEDULE[current_trial];
    }
    else
    {
      Serial.println("Invalid solenoid value");
      return;
    }
  }

  int quotient = duration / 10000; // delayMicroseconds only allows for values up to 16383, we use multiple instances of 
  // 10000 to avoid overflow

  int remaining_delay = duration - (quotient * 10000);  

  
  toggle_solenoid(valve_side, solenoids[valve_number]);

  for (int i = 0; i < quotient; i++)
  {
    delayMicroseconds(10000);
  }

  delayMicroseconds(remaining_delay); // we add the remaining delay to the end of the loop to ensure the total duration is correct
  untoggle_solenoid(valve_side, solenoids[valve_number]);
  interrupts();

}

void myISR() 
{
  valve_side = (PINH & (1 << PH5)) >> PH5;

  lick_available = true;

}

void setup() 
{
  stepper.setMaxSpeed(5500);
  stepper.setAcceleration(5500);
  Serial.begin(115200);

  // Check if EEPROM is initialized
  if (!checkEEPROMInitialized()) 
  {
      // Initialize with default values
      for (int i = 0; i < 8; i++) 
      {
          side_one_lick_durations[i] = 24125; // Default value
          side_two_lick_durations[i] = 24125; // Default value
      }

      writeValuesToEEPROM(side_one_lick_durations, DATA_START_ADDRESS, 8);
      writeValuesToEEPROM(side_two_lick_durations, DATA_START_ADDRESS + 8 * sizeof(long int), 8);
      markEEPROMInitialized();
      Serial.println("EEPROM initialized with default values.");
  }
  else 
  {
      // Read the existing values from EEPROM
      readValuesFromEEPROM(side_one_lick_durations, DATA_START_ADDRESS, 8);
      readValuesFromEEPROM(side_two_lick_durations, DATA_START_ADDRESS + 8 * sizeof(long int), 8);
      //Serial.println("Values read from EEPROM.");
  }

  DDRA |= (255); // Set pins 22-29 as outputs
  DDRC |= (255); // Set pins 30-37 as outputs 
  
  pinMode(2, INPUT_PULLUP);
  pinMode(8, INPUT_PULLUP);
  pinMode(9, INPUT_PULLUP);
  pinMode(10, INPUT_PULLUP);
  pinMode(11, INPUT_PULLUP);
  pinMode(12, INPUT_PULLUP);

  // // Attach the interrupt
  attachInterrupt(0, myISR, RISING); // attach interrupt on pin 2

}

void prime_valves()
{
  for(int i = 0; i < 1000; i++)
  {
    Serial.println(i);
    open_start = millis();
    PORTD |= (1 << PD7); // Set pin 38 to HIGH (Valve 1)
    // max value of delayMicroseconds is 16383, using smaller multiples of 10000 to avoid overflow
    delayMicroseconds(10000);
    delayMicroseconds(10000);
    delayMicroseconds(10000);
    delayMicroseconds(7500);
    
    CLEAR_BIT(PORTD, PD7); // Set pin 38 to LOW (close)
    
    delay(25);
    close_time = millis();
    valve_open_time_d += (close_time - open_start);

    open_start = millis();
    
    SET_BIT(PORTC, PC7); // Set pin 30 to HIGH (valve 2)

    delayMicroseconds(10000);
    delayMicroseconds(10000);
    delayMicroseconds(4125);
    PORTC &= ~(1 << PC7); // Set pin 30 to low (close)
    delay(25);
    close_time = millis();
    valve_open_time_c += (close_time - open_start);

    delay(100);
  } 
    Serial.print("Valve one opened for: ");
    Serial.print(valve_open_time_d);
    Serial.println(" milliseconds.");
    Serial.print("Valve two opened for: ");
    Serial.print(valve_open_time_c);
    Serial.println(" milliseconds.");
}

void test_volume()
{

  while (Serial.available() == 0) {}
  
    String recieved_transmission = Serial.readStringUntil('\n');

    int num_valves = recieved_transmission.toInt();
    Serial.println("");
    Serial.println("start");
    for(int i=0; i < num_valves / 2; i++)
    {
      while(true)
      {
        while (Serial.available() == 0) {}

        recieved_transmission = Serial.readStringUntil('\n');

        if(recieved_transmission == "continue")
        {
          break;
        }
      }

      for(int j=0; j < 500; j++)
      {
        lick_handler(0, i);
        lick_handler(1, i);
        delay(100);
      }
      clear_serial_buffer();
      delay(100);
      Serial.println("Finished loop");

    }
    

    delay(500);
    clear_serial_buffer();
    Serial.println("side one");


    for (int i = 0; i < (num_valves / 2); i++) 
    {

      Serial.println(side_one_lick_durations[i]);
      delay(50); // Short delay to ensure Python can keep up
    }
    
    Serial.println("end side one");

    Serial.println("side two");

    for (int i = 0; i < (num_valves / 2); i++) 
    {
      Serial.println(side_two_lick_durations[i]);
      delay(50); // Short delay to ensure Python can keep up
    }

    Serial.println("end side two");

} 

void recieve_schedule(int side)
{

  if(side == 1)
  {
    // Wait until data is available
    while (Serial.available() == 0) {}

    // Now read the data
    String valvePairStr = Serial.readStringUntil('\n');
    // Echo back the received data
    Serial.print(valvePairStr);

    int position = valvePairStr.toInt();

    // Example call
    addToArray(SIDE_ONE_SCHEDULE, side_one_size, position);

    // Wait a little bit for the Python side to be ready to receive
    delay(100); // Delay for 100 milliseconds

  }
  if(side == 2)
  {
    while (Serial.available() == 0) {}

    // Now read the data
    String valvePairStr = Serial.readStringUntil('\n');
   // Echo back the received data
    Serial.print(valvePairStr);
    int position = valvePairStr.toInt();

    addToArray(SIDE_TWO_SCHEDULE, side_two_size, position);

    // Wait a little bit for the Python side to be ready to receive
    delay(100); // Delay for 100 milliseconds
  }
}

void send_schedule_back(int side) {
  if (side == 1) 
  {
    for (int i = 0; i < side_one_size; i++) 
    {
      Serial.println(SIDE_ONE_SCHEDULE[i]);
      delay(50); // Short delay to ensure Python can keep up
    }
    Serial.println("end side one");
  } 
  else if (side == 2) 
  {
    for (int i = 0; i < side_two_size; i++) 
    {
      Serial.println(SIDE_TWO_SCHEDULE[i]);
      delay(50); // Short delay to ensure Python can keep up
    }
    Serial.println("end");
  } 
  else 
  {
    Serial.println("Invalid Side for Schedule Transmission");
  }
}

void update_opening_times()
{
    long int durations[16]; 

    int current_element = 0;
    int current_element_in_side = 0;


    while(true)
    {
    // Wait until data is available
    while (Serial.available() == 0) {}

    // Now read the data
    String identifier = Serial.readStringUntil('\n');
    // Echo back the received data
    Serial.print(identifier);

    if(identifier == "end") 
    {
      break;
    }

    int ident_int = identifier.toInt();

    if(ident_int == 1)
    {
    while (Serial.available() == 0) {}
    String duration = Serial.readStringUntil('\n');
    int new_duration = duration.toInt();

    if(new_duration == side_one_lick_durations[current_element_in_side])
    {
      durations[current_element] = side_one_lick_durations[current_element_in_side];
    }
    else
    {
      durations[current_element] = new_duration; 
    }

    current_element++;
    current_element_in_side++;
    }

    current_element_in_side = 0;

    if(ident_int == 2)
    {
    while (Serial.available() == 0) {}
    String duration = Serial.readStringUntil('\n');
    int new_duration = duration.toInt();

    if(new_duration == side_two_lick_durations[current_element_in_side])
    {
      durations[current_element] = side_two_lick_durations[current_element_in_side];
    }
    else
    {
      durations[current_element] = new_duration; 
    }

    current_element++;
    current_element_in_side++;
    }
    }


    // Wait a little bit for the Python side to be ready to receive
    delay(100); // Delay for 100 milliseconds
    writeValuesToEEPROM(durations, DATA_START_ADDRESS, current_element + 1);
}



void loop() 
{
  if(lick_available)
  {
    Serial.print(valve_side);
    lick_handler(valve_side);
    lick_available = false;
  }

  char command = '\0';

  if (Serial.available() > 0) {
      command = Serial.read();
  }
  
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
      test_volume();
      break;
    case 'F':
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
    case '1':
    {
      recieve_schedule(1);

      break;
    }
    case '2':
    {
      recieve_schedule(2);
      break;
    }
    case 'S':
    {
      send_schedule_back(1); // Send Side One schedule
      delay(100); 
      send_schedule_back(2); // Send Side Two schedule
      break;
    }
    case 'P':
    {
      readValuesFromEEPROM(side_one_lick_durations, DATA_START_ADDRESS, 8);
      readValuesFromEEPROM(side_two_lick_durations, DATA_START_ADDRESS + 8 * sizeof(long int), 8);
      break;
    }
    case 'V':
    {
      update_opening_times();
    }
    
    default:
      break;
  }


  stepper.run();
}
