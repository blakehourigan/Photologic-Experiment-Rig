#include <Arduino.h>
#include <avr/io.h>
#include <avr/wdt.h>

// side one defs
#define SIDE_ONE_READ PINC
#define SIDE_ONE_WRITE PORTC

#define OPTICAL_DETECTOR_BIT_SIDE1 PC6   // digital 31, from photologic
#define LED_BIT_SIDE1 PC4  // digital 33, to LED for side 1

// side two defs
#define SIDE_TWO_READ PINA
#define SIDE_TWO_WRITE PORTA

#define OPTICAL_DETECTOR_BIT_SIDE2 PA1   // digital 23, from photologic
#define LED_BIT_SIDE2 PA3  // digital 25, to led for side 2

// lick signal defs
#define LICK_SIGNAL_WRITE PORTH
#define LICK_SIGNAL_READ PINH
#define LICK_SIGNAL_BIT PH4   // digital 7, to lick signal
#define LICK_SIDE_BIT PH5

unsigned long start_time, end_time; // Variables to store start and end time of licks
unsigned long program_start;
unsigned long current_time; 
static unsigned long flipStartTime = 0;

volatile bool side_1_pin_state, side_2_pin_state;

volatile bool side_1_previous_state = 1; 
volatile bool side_2_previous_state = 1; 

unsigned int side_1_licks = 0; // Variable to store number of licks detected
unsigned int side_2_licks = 0;

bool open_valves = false; // Variable to store whether to open valves or not

String side; 

void setup() 
{
  Serial.begin(115200); // Start the serial communication
  
  // Set the pins to high impedance
  DDRH |= (1 << LICK_SIGNAL_BIT);
  DDRH |= (1 << LICK_SIDE_BIT);

  DDRC |= (1 << LED_BIT_SIDE1);
  DDRA |= (1 << LED_BIT_SIDE2);

  SIDE_ONE_WRITE |= (1 << LED_BIT_SIDE1);
  SIDE_TWO_WRITE |= (1 << LED_BIT_SIDE2);


  cli(); // Disable global interrupts
  
  // Set up Timer 4 for 50ms interval
  TCCR4A = 0; // Set entire TCCR4A register to 0
  TCCR4B = 0; // Set entire TCCR4B register to 0
  TCNT4 = 0; // Initialize counter value to 0
  unsigned long int compare_match = 800000;
  OCR4A = compare_match; // Set compare match register for 50ms intervals
  TCCR4B |= (1 << WGM42); // Turn on CTC mode
  TCCR4B |= (1 << CS40); // Set prescaler to 1 (no prescaling)

  sei(); // Enable global interrupts
  program_start = millis();
}

ISR(TIMER4_COMPA_vect) 
{
  side_1_pin_state = (SIDE_ONE_READ & (1 << OPTICAL_DETECTOR_BIT_SIDE1));
  side_2_pin_state = (SIDE_TWO_READ & (1 << OPTICAL_DETECTOR_BIT_SIDE2));
}

void loop() 
{
  check_serial_command();
  
  char side_one[5] = "One";
  char side_two[5] = "Two";

  detect_licks(side_one, side_1_pin_state, side_1_previous_state, side_1_licks, LED_BIT_SIDE1);
  detect_licks(side_two, side_2_pin_state, side_2_previous_state, side_2_licks, LED_BIT_SIDE2);

  update_leds();

}

void update_leds() 
{    
  if (side_1_pin_state) 
  {
    SIDE_ONE_WRITE |= (1 << LED_BIT_SIDE1); // Turn on LED for side 1
  } 
  else
  {
    SIDE_ONE_WRITE &= ~(1 << LED_BIT_SIDE1); // Turn off LED for side 1
  }

  if (side_2_pin_state) 
  {
    SIDE_TWO_WRITE |= (1 << LED_BIT_SIDE2); // Turn on LED for side 2
  } 
  else 
  {
    SIDE_TWO_WRITE &= ~(1 << LED_BIT_SIDE2); // Turn off LED for side 2
  }
}


void check_serial_command() 
{
  char command = '\0';

  if (Serial.available() > 0) {
      command = Serial.read();
  }
  
  switch (command) 
  {
    case 'R': // reset the arduino
      wdt_enable(WDTO_1S);
      break;
    case 'W' :
      Serial.println("LASER");
      break;
    case 'B': // begin opening valves from this point forware
      open_valves = true;
      break;
    case 'E': // stop opening valves
      open_valves = false;
      break;
    case 'S':
      cli();
      TIMSK4 |= (1 << OCIE4A); // Enable timer compare interrupt
      sei();
      break;
    default:
      break;
  } 
}


void check_side_and_port(char *side)
{
if(strcmp(side, "One") == 0)
{
LICK_SIGNAL_WRITE |= (0 << LICK_SIDE_BIT); // Keep the first pin low
}
else if(strcmp(side, "Two"))
{
LICK_SIGNAL_WRITE |= (1 << LICK_SIDE_BIT); // Set the first pin high
}

LICK_SIGNAL_WRITE |= (1 << LICK_SIGNAL_BIT); // Set the bit high
flipStartTime = micros();
}

void reset_side_and_port()
{
  LICK_SIGNAL_WRITE &= ~(1 << LICK_SIDE_BIT); // Set the first pin low

  LICK_SIGNAL_WRITE &= ~(1 << LICK_SIGNAL_BIT); // Set the bit low
}

void detect_licks(char *side, volatile bool& current_state, volatile bool& previous_state, unsigned int& licks, byte output_bit) 
{
    
    if (current_state == 0 && previous_state == 1) 
    {
        start_time = millis();
        if (open_valves) 
        {
          check_side_and_port(side);
        }
        previous_state = 0;
    } 
    else if (current_state == 1 && previous_state == 0) 
    {
        end_time = millis();
        licks++;
        send_lick_details(licks, start_time, end_time, side);
        previous_state = 1;
    }
    
    if (open_valves)
    {
      if( micros() - flipStartTime >= 10) // after 10 microseconds, reset signals
      { 
      reset_side_and_port();
      }
    }

}

void send_lick_details(unsigned int licks, unsigned long start_time, unsigned long end_time, char *side)
 {
<<<<<<< Updated upstream
    Serial.print("Stimulus ");
    Serial.println(side);
=======
    char side_indicator[50]; 
    sprintf(side_indicator, "<Stimulus %s>", side);

    Serial.println(side_indicator);
>>>>>>> Stashed changes
}
