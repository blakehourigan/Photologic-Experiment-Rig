#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include <avr/wdt.h>
#include "Arduino.h"

class valve_control 
{
public:
  void toggle_solenoid(int side, int *side_one_schedule, int *side_two_schedule, int current_trial, bool testing = false, int valve = -1);
  void untoggle_solenoids();
  void lick_handler(int valve_side, int *side_one_schedule, int *side_two_schedule, \
                    unsigned long *side_one_durations, unsigned long *side_two_durations, int current_trial, \
                    bool testing = false, int valve_number = -1);

private:
  static const int side_one_solenoids[];
  static const int side_two_solenoids[];

  void toggle_bit(volatile uint8_t& port, uint8_t bit);
  void clear_bit(volatile uint8_t& port, uint8_t bit);
};

#endif