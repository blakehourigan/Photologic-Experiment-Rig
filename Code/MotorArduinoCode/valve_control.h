#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include <avr/wdt.h>

class valve_control {
public:
  void toggle_solenoid(int valve_num, volatile uint8_t *PORT);
  void untoggle_solenoids();
  void lick_handler(int valve_number, long int valve_duration,
                    volatile uint8_t *PORT);
  void lick_handler(int valve_num, long int valve_duration);

private:
  static const int side_one_solenoids[];
  static const int side_two_solenoids[];

  void toggle_bit(volatile uint8_t &port, uint8_t bit);
  void clear_bit(volatile uint8_t &port, uint8_t bit);
};

#endif
