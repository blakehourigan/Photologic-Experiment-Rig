#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include <avr/wdt.h>

class valve_control {
public:
  void toggle_solenoid(uint8_t valve_num, volatile uint8_t *PORT);
  void untoggle_solenoids();
  void lick_handler(uint8_t valve_num, unsigned long valve_duration,
                    volatile uint8_t *PORT);

private:
  static const int side_one_solenoids[];
  static const int side_two_solenoids[];

  void toggle_bit(volatile uint8_t &port, uint8_t bit);
  void clear_bit(volatile uint8_t &port, uint8_t bit);
};

#endif
