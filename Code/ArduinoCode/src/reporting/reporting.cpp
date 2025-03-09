#include "reporting.h"

void report_motor_movement(String previous_command,
                           doorMotorTimeDetails motor_time,
                           unsigned long program_start_time,
                           unsigned long trial_start) {
  /*
  This function is called when the door finishes a movement operation. It takes
  the previous command as a parameter and tells the python controller that a
  movement has completed and which type of movement that was, so that we can
  mark these movements down in the lick dataframe. If the movement was up, that
  means a trial just ended and we can increment to the next trial.
  */

  motor_time.movement_duration =
      motor_time.movement_end - motor_time.movement_start;

  // time of motor movement ending relative to program start
  motor_time.end_rel_to_start = motor_time.movement_end - program_start_time;

  motor_time.end_rel_to_trial = motor_time.movement_end - trial_start;

  Serial.print("MOTOR");
  Serial.print("|");
  Serial.print(motor_time.movement_type);
  Serial.print("|");
  Serial.print(motor_time.movement_duration);
  Serial.print("|");
  Serial.print(motor_time.end_rel_to_start);
  Serial.print("|");
  // printline to force data out
  Serial.println(motor_time.end_rel_to_trial);
}

void report_ttc_lick(uint8_t side, lickTimeDetails lick_time,
                     unsigned long program_start_time,
                     unsigned long trial_start) {
  /* Function to report lick occurance and occompanying details such as lick
   * side, length of time tongue broke the beam.
   * we use pipes '|' to separate different data points.
   */
  lick_time.lick_duration = lick_time.lick_end_time - lick_time.lick_begin_time;

  lick_time.onset_rel_to_start = lick_time.lick_begin_time - program_start_time;

  lick_time.onset_rel_to_trial = lick_time.lick_begin_time - trial_start;

  if (lick_time.lick_duration < LICK_THRESHOLD) {
    // if a lick duration does not meet the LICK_THRESHOLD, disregard it
    return;
  }

  Serial.print(side);
  Serial.print("|");
  Serial.print(lick_time.lick_duration);
  Serial.print("|");
  Serial.print(lick_time.onset_rel_to_start);
  Serial.print("|");
  // printline to force data out
  Serial.println(lick_time.onset_rel_to_trial);
}

void report_sample_lick(uint8_t side, lickTimeDetails lick_time,
                        valveTimeDetails valve_time,
                        unsigned long program_start_time,
                        unsigned long trial_start) {
  /* Function to report lick occurance and occompanying details such as lick
   * side, length of time tongue broke the beam, duration of the valve opening
   * we use pipes '|' to separate different data points.
   */

  // calc lick time from break beam -> clear beam and valve time from valve open
  // -> valve close
  lick_time.lick_duration = lick_time.lick_end_time - lick_time.lick_begin_time;
  valve_time.valve_duration =
      valve_time.valve_close_time - valve_time.valve_open_time;

  lick_time.onset_rel_to_start = lick_time.lick_begin_time - program_start_time;

  lick_time.onset_rel_to_trial = lick_time.lick_begin_time - trial_start;

  // if a lick duration does not meet the LICK_THRESHOLD, disregard it
  if (lick_time.lick_duration < LICK_THRESHOLD) {
    return;
  }

  Serial.print(side);
  Serial.print("|");
  Serial.print(lick_time.lick_duration);
  Serial.print("|");
  Serial.print(valve_time.valve_duration);
  Serial.print("|");
  Serial.print(lick_time.onset_rel_to_start);
  Serial.print("|");
  // printline to force data out
  Serial.println(lick_time.onset_rel_to_trial);
}
