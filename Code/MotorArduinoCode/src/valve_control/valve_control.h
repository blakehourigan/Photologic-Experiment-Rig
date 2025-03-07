#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include <avr/wdt.h>

extern unsigned long valve_open_time;
extern unsigned long valve_close_time;
extern unsigned long total_valve_duration;

void toggle_solenoid(uint8_t valve_num, volatile uint8_t *PORT);
void untoggle_solenoids();
void lick_handler(uint8_t valve_num, unsigned long valve_duration,
                  volatile uint8_t *PORT);

void toggle_bit(volatile uint8_t &port, uint8_t bit);
void clear_bit(volatile uint8_t &port, uint8_t bit);

#endif
