#ifndef TIME_DETAILS_H

#define TIME_DETAILS_H

#include <Arduino.h>

struct lickTimeDetails {
  unsigned long lick_begin_time;
  unsigned long lick_end_time;

  unsigned long valve_open_time;
  unsigned long valve_close_time;
};

struct doorMotorTimeDetails {
  unsigned long movement_start;
  unsigned long movement_end;
  String direction;
};

#endif // !TIME_DETAILS_H
