#include <AccelStepper.h>
#include <avr/wdt.h>

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
volatile int pin0, pin1, pin2, pin3;
bool lick_available = false;

long int side_one_lick_duration = 37500; // 37.5 milliseconds vale 1 
long int side_two_lick_duration = 24125; // 24.125 milliseconds valve 2  

const int MAX_SIZE = 50; // Maximum size of the array
int side_one_size = 0; // Keep track of the current number of elements
int side_two_size = 0;

AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);


// Function to add an element to the array
void addToArray(int *array,  int element, int size) {
  if (size < MAX_SIZE) {
    array[size] = element; // Add element at the next available index
    size++; // Increment the size counter
  } else {
    // Array is full, handle error or ignore
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

void lick_handler(int valve_side)
{
  const int * solenoids;
  long int duration = 0;
  int valve_number = -1; 

  noInterrupts();

  if(valve_side == 0)
  {
    duration = side_one_lick_duration;
    solenoids = SIDE_ONE_SOLENOIDS;
    valve_number = SIDE_ONE_SCHEDULE[current_trial];
  }
  else if(valve_side == 1)
  {
    duration = side_two_lick_duration;
    solenoids = SIDE_TWO_SOLENOIDS;
    valve_number = SIDE_TWO_SCHEDULE[current_trial];
  }
  else
  {
    Serial.println("Invalid solenoid value");
    return;
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

void test_valve_operation() 
{
    // Set pin 38 as an output
    DDRD |= (1 << PD7);

    // Open the valve
    PORTD |= (1 << PD7); 
    unsigned long start_time = millis();

    // Wait for 3 minutes (180000 milliseconds)
    while(millis() - start_time < 150000) {
        // Keep the loop running for 3 minutes
    }

    // Close the valve
    PORTD &= ~(1 << PD7);
    unsigned long end_time = millis();

    // Calculate duration
    unsigned long duration = end_time - start_time;
  
    // Print the duration
    Serial.print("Time valve was open: ");
    Serial.print(duration);
    Serial.println(" milliseconds");
}


// this function needs rewritten it probably doesn't work at all
void test_volume()
{
  DDRC |= (1 << PC7); // Set pin 30 as an output
  DDRD |= (1 << PD7); // Set pin 30 as an output

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

void recieve_schedule(int side)
{

  if(side == 1)
  {
    // Wait until data is available
    while (Serial.available() == 0) 
    {
    }


    // Now read the data
    String valvePairStr = Serial.readStringUntil('\n');
    // Echo back the received data
    Serial.println(valvePairStr);

    int position = valvePairStr.toInt();

    addToArray(SIDE_ONE_SCHEDULE, position, side_one_size);

    // Wait a little bit for the Python side to be ready to receive
    delay(100); // Delay for 100 milliseconds

  }
  if(side == 2)
  {
    while (Serial.available() == 0) 
    {
    }

    // Now read the data
    String valvePairStr = Serial.readStringUntil('\n');
   // Echo back the received data
    Serial.print(valvePairStr);
    int position = valvePairStr.toInt();

    addToArray(SIDE_TWO_SCHEDULE, position, side_two_size);

    // Wait a little bit for the Python side to be ready to receive
    delay(100); // Delay for 100 milliseconds
  }
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
      test_valve_operation();
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

    default:
      break;
  }


  stepper.run();
}
