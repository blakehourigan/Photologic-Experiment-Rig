#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include <avr/wdt.h>
#include "EEPROM_INTERFACE.h"

class valve_control 
{
public:
  void toggle_solenoid(int side, int *side_one_schedule, int *side_two_schedule, int current_trial);
  void untoggle_solenoids();
  void lick_handler(int valve_side, int *side_one_schedule, int *side_two_schedule, int current_trial, EEPROM_INTERFACE& eeprom, int valve_number = -1);
  void prime_valves(bool prime_flag, int *side_one_schedule, int *side_two_schedule, int current_trial, EEPROM_INTERFACE& eeprom);


private:
  static const int side_one_solenoids[];
  static const int side_two_solenoids[];

  void toggle_bit(volatile uint8_t& port, uint8_t bit);
  void clear_bit(volatile uint8_t& port, uint8_t bit);
};

#endif