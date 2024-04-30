#include "valve_control.h"

const int valve_control::side_one_solenoids[] = {PA0, PA1, PA2, PA3, PA4, PA5, PA6, PA7};
const int valve_control::side_two_solenoids[] = {PC7, PC6, PC5, PC4, PC3, PC2, PC1, PC0};

void valve_control::toggle_bit(volatile uint8_t& port, uint8_t bit) {
  port ^= (1 << bit);
}

void valve_control::clear_bit(volatile uint8_t& port, uint8_t bit) {
  port &= ~(1 << bit);
}

void valve_control::toggle_solenoid(int side, int solenoid_pin) {
  if (side == 0) {
    toggle_bit(PORTA, solenoid_pin);
  } else if (side == 1) {
    toggle_bit(PORTC, solenoid_pin);
  }
}

void valve_control::untoggle_solenoid(int side, int solenoid_pin) {
  if (side == 0) {
    clear_bit(PORTA, solenoid_pin);
  } else if (side == 1) {
    clear_bit(PORTC, solenoid_pin);
  }
}

void valve_control::lick_handler(int valve_side, int *side_one_schedule, int *side_two_schedule, int current_trial, EEPROM_INTERFACE& eeprom, int valve_number) {
  const int *solenoids = (valve_side == 0) ? side_one_solenoids : side_two_solenoids;
  unsigned long int valve_duration = 0;

  noInterrupts();

  int address = (valve_side == 0) ? eeprom.DATA_START_ADDRESS : eeprom.SIDE_TWO_DURATIONS_ADDRESS;

  if (valve_number == -1) {
    valve_number = (valve_side == 0) ? side_one_schedule[current_trial] : side_two_schedule[current_trial];
  }

  eeprom.read_single_value_from_EEPROM(valve_duration, address, valve_number);

  int quotient = valve_duration / 10000;
  int remaining_delay = valve_duration - (quotient * 10000);

  toggle_solenoid(valve_side, solenoids[valve_number]);

  for (int i = 0; i < quotient; i++) {
    delayMicroseconds(10000);
  }

  delayMicroseconds(remaining_delay);
  untoggle_solenoid(valve_side, solenoids[valve_number]);

  interrupts();
}

void valve_control::prime_valves(bool prime_flag, int *side_one_schedule, int *side_two_schedule, int current_trial, EEPROM_INTERFACE& eeprom)
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
                  lick_handler(side, side_one_schedule, side_two_schedule, current_trial, eeprom, valve_number);
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