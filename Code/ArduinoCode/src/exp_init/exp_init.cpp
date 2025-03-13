#include "exp_init.h"

// experiment related variables
uint8_t num_stimuli = 0;
uint8_t num_trials = 0;

void receive_exp_variables() {
  /* function to recieve program variables such as num_stimuli
   * and num_trials.
   *
   * num stimuli will be sent in the first byte, while num_trials
   * will follow behind
   */
  // if we have 2 bytes available, read number_stimuli in
  num_stimuli = 0;
  num_trials = 0;
  // wait until we know that both bytes have arrived sequentially.
  while (Serial.available() < 2) {
  }
  // once they are read one byte at a time into repective variables
  num_stimuli = Serial.read();

  num_trials = Serial.read();
}

ValveSchedules receive_schedules() {
  ValveSchedules schedules;

  ExpScheduleArray side_one_arr;
  ExpScheduleArray side_two_arr;

  // when this variable equals num trials, sd_one has been recieved,
  // move on to side two
  int elements_processed = 0;
  // holds current valve number being processed
  int valve = 0;
  // processing side one first
  int side = 1;

  while (1) {
    // if we have any serial bytes available, read one byte in and
    // say that this byte represents which valve to select for this trial
    if (Serial.available() > 0) {
      valve = Serial.read();
      elements_processed++;

      if (side == 1) {
        side_one_arr.append(valve);
      } else if (side == 2) {
        side_two_arr.append(valve);
      }
      if (elements_processed == num_trials) {
        if (side == 1) {
          elements_processed = 0;
          side = 2;
        } else {
          break;
        }
      }
    }
  }
  schedules.side_one = side_one_arr;
  schedules.side_two = side_two_arr;
  schedules.schedules_recieved = true;
  return schedules;
}

ValveDurations receive_durations() {

  DurationsArray side_one;
  DurationsArray side_two;

  ValveDurations durations;

  // when this variable equals MAX_VALVES_PER_SIDE, sd_one has been recieved,
  // move on to side two
  int elements_processed = 0;
  // holds current valve number being processed
  unsigned long byte0 = 0;
  unsigned long byte1 = 0;
  unsigned long byte2 = 0;
  unsigned long byte3 = 0;

  unsigned long duration = 0;

  // processing side one first
  int side = 1;

  while (1) {
    // if we have any serial bytes available, read one byte in and
    // say that this byte represents which valve to select for this trial
    if (Serial.available() > 3) {
      byte0 = Serial.read();
      byte1 = Serial.read();
      byte2 = Serial.read();
      byte3 = Serial.read();

      duration = byte0 | (byte1 << 8) | (byte2 << 16) | (byte3 << 24);

      elements_processed++;

      if (side == 1) {
        side_one.append(duration);
      } else if (side == 2) {
        side_two.append(duration);
      }

      if (elements_processed == MAX_VALVES_PER_SIDE) {
        if (side == 1) {
          elements_processed = 0;
          side = 2;
        } else {
          break;
        }
      }
    }
  }

  durations.side_one = side_one;
  durations.side_two = side_two;
  durations.durations_recieved = true;
  return durations;
}

void schedule_verification(ValveSchedules schedules) {
  ExpScheduleArray side_one = schedules.side_one;
  ExpScheduleArray side_two = schedules.side_two;

  // echo recieved schedules to python controller, so that it can verify
  // that we received them correctly
  for (int i = 0; i < side_one.len; i++) {
    Serial.write(side_one.schedule[i]);
  }

  for (int i = 0; i < side_two.len; i++) {
    Serial.write(side_two.schedule[i]);
  }
  // force all the data out
  Serial.flush();

  // Serial.println("Schedule sent back for verification.");
}

void durations_verification(ValveDurations durations) {
  DurationsArray side_one = durations.side_one;
  DurationsArray side_two = durations.side_two;
  // echo recieved schedules to python controller, so that it can verify that
  // we received them correctly
  unsigned long val = 0;
  for (int i = 0; i < side_one.len; i++) {
    //
    val = side_one.durations[i];
    Serial.write((uint8_t *)&val, sizeof(val));
  }

  for (int i = 0; i < side_two.len; i++) {
    val = side_two.durations[i];
    Serial.write((uint8_t *)&val, sizeof(val));
  }
  // force all the data out
  Serial.flush();
}
