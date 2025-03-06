#include <Arduino.h>
#include <avr/io.h>
#include <avr/wdt.h>

// digital 31, from photologic
#define OPTICAL_DETECTOR_BIT_SIDE1 PC6
// digital 33, to LED for side 1
#define LED_BIT_SIDE1 PC4

// side two definitions
// digital 23, from photologic
#define OPTICAL_DETECTOR_BIT_SIDE2 PA1
// digital 25, to led for side 2
#define LED_BIT_SIDE2 PA3

// digital 7, to lick signal
#define LICK_SIGNAL_BIT PH4
#define LICK_SIDE_BIT PH5

// Debounce time in milliseconds
#define DEBOUNCE_TIME 50

// Variables to store start and end time of licks
extern unsigned long lick_start_time;
extern unsigned long lick_end_time;
extern unsigned long last_debounce_time;

extern unsigned long flipStartTime = 0;

extern volatile bool side_1_pin_state;
extern volatile bool side_2_pin_state;

extern volatile bool side_1_previous_state = 1;
extern volatile bool side_2_previous_state = 1;

// Variable to store number of licks detected
extern unsigned int side_1_licks = 0;
extern unsigned int side_2_licks = 0;
extern unsigned int total_licks = 0;

// stores whether motor should open valves or not
extern bool open_valves = false;

extern uint8_t side_one = 0;
extern uint8_t side_two = 1;

void setup() {
  // Start the serial communication
  Serial.begin(115200);

  // Set the LICK SIGNAL, LICK SIDE, and LED pins as output pins via the data
  // direction register for
  // H
  DDRH |= (1 << LICK_SIGNAL_BIT);
  DDRH |= (1 << LICK_SIDE_BIT);

  // set the data direction register to output on pin 5 of the C register
  DDRC |= (1 << LED_BIT_SIDE1);
  // set the data direction register to output on pin 4 of the A register
  DDRA |= (1 << LED_BIT_SIDE2);

  // side one led is on portc pin 5
  PORTC |= (1 << LED_BIT_SIDE1);
  // side two led bit is on portA pin 4
  PORTA |= (1 << LED_BIT_SIDE2);

  // Enable global interrupts
  sei();
}

void loop() {
  String command = "\0";

  if (Serial.available() > 0) {
    // read until the newline char
    command = Serial.readStringUntil('\n');
  }

  // only process command cases if one has been recieved from the controller
  if (!command.equals("\0")) {
    // reset the board
    if (command.equals("RESET")) {
      wdt_enable(WDTO_1S);
    }
    // Who are you? used for identification with python
    else if (command.equals("WHO ARE YOU")) {
      Serial.println("LASER");
    }
    // begin opening valves from this point forward
    else if (command.equals("BEGIN OPEN VALVES")) {
      open_valves = true;
    }
    // stop opening valves
    else if (command.equals("STOP OPEN VALVES")) {
      open_valves = false;
    } else if (command.equals("PRINT TOTAL LICKS")) {
      Serial.println(total_licks);
    }
  }

  side_1_pin_state = (PINC & (1 << OPTICAL_DETECTOR_BIT_SIDE1));
  side_2_pin_state = (PINA & (1 << OPTICAL_DETECTOR_BIT_SIDE2));

  detect_licks(side_one, side_1_pin_state, side_1_previous_state, side_1_licks);
  detect_licks(side_two, side_2_pin_state, side_2_previous_state, side_2_licks);

  update_leds();
}

void update_leds() {
  if (side_1_pin_state) {
    // Turn on LED for side 1
    PORTC |= (1 << LED_BIT_SIDE1);
  } else {
    // Turn off LED for side 1, indicating a lick
    PORTC &= ~(1 << LED_BIT_SIDE1);
  }

  if (side_2_pin_state) {
    // Turn on LED for side 2
    PORTA |= (1 << LED_BIT_SIDE2);
  } else {
    // Turn off LED for side 2, indicating a lick
    PORTA &= ~(1 << LED_BIT_SIDE2);
  }
}

void signal_side_and_port(uint8_t side) {
  if (side == 0) {
    // Set the side pin low (0), indicating side is 1
    PORTH |= (0 << LICK_SIDE_BIT);
  }

  else if (side == 1) {
    // Set the side pin high (1), indicating side is 2
    PORTH |= (1 << LICK_SIDE_BIT);
  }
  // indicate that a lick is available to the motor arduino by setting lick
  // signal high (1)
  PORTH |= (1 << LICK_SIGNAL_BIT);
  flipStartTime = micros();
}

void detect_licks(uint8_t side, volatile bool &current_state,
                  volatile bool &previous_state, unsigned int &licks) {
  unsigned long current_time = millis();

  // only perform this action if it has been 50ms or more since the last call
  if ((current_time - last_debounce_time) > DEBOUNCE_TIME) {
    // tongue has broken beam, lick begins
    if (current_state == 0 && previous_state == 1) {
      lick_start_time = millis();
      if (open_valves) {
        signal_side_and_port(side);
      }
      previous_state = 0;
      last_debounce_time = current_time;
      // tongue has cleared the beam, lick ended
    } else if (current_state == 1 && previous_state == 0) {
      lick_end_time = millis();

      licks++;
      total_licks++;

      send_lick_details(side, lick_start_time, lick_end_time);

      previous_state = 1;
      last_debounce_time = current_time;
    }
  }

  if (open_valves) {
    // after 10 microseconds, reset signals
    if (micros() - flipStartTime >= 10) {
      // by resetting PORTH to 0, we set all pins to zero, which
      // resets LICK_SIGNAL_BIT to 0 and LICK_SIDE_BIT to zero.
      PORTH = 0;
    }
  }
}

void send_lick_details(uint8_t side, unsigned long lick_start_time,
                       unsigned long lick_end_time) {
  char side_indicator[50];
  char lick_length[10];

  const char *side_str;

  unsigned long lick_len = lick_end_time - lick_start_time;

  if (side == 0) {
    side_str = "ONE";
  } else if (side == 1) {
    side_str = "TWO";
  }

  sprintf(side_indicator, "STIMULUS %s", side_str);

  sprintf(lick_length, "%lu", lick_len);

  // we use println here becuase we read until newlines in the python program
  Serial.print(side_indicator);
  Serial.print("|");
  Serial.println(lick_length);
}
