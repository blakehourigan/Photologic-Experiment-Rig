#include "exp_init.h"

// experiment related variables
uint8_t num_stimuli = 0;
uint8_t num_trials = 0;

unsigned long side_one_durations[VALVES_PER_SIDE];
unsigned long side_two_durations[VALVES_PER_SIDE];

Vector<unsigned long> side_one_dur_vec = side_one_durations;
Vector<unsigned long> side_two_dur_vec = side_two_durations;

uint8_t side_one_schedule[MAX_SCHEDULE_SIZE];
uint8_t side_two_schedule[MAX_SCHEDULE_SIZE];

Vector<uint8_t> side_one_sched_vec = side_one_schedule;
Vector<uint8_t> side_two_sched_vec = side_two_schedule;

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

void receive_schedules() {
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
        side_one_sched_vec.push_back(valve);
      } else if (side == 2) {
        side_two_sched_vec.push_back(valve);
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
}

// void receive_durations() {
//
//
//
//     int cur_trial = doc["current_trial"];
//     JsonArray valve_durations_side_one = doc["valve_durations_side_one"];
//     JsonArray valve_durations_side_two = doc["valve_durations_side_two"];
//
//     // Update the global variables
//     side_one_size = side_one_schedule.size();
//     side_two_size = side_two_schedule.size();
//
//
//     // Resize and populate the SIDE_ONE_SCHEDULE array
//     side_one_durations = new unsigned long[VALVES_SIDE_ONE];
//
//     for (int i = 0; i < VALVES_SIDE_ONE; i++) {
//         side_one_durations[i] = valve_durations_side_one[i].as<int>();
//     }
//
//     // create new array for side_two_durations
//     side_two_durations = new unsigned long[VALVES_SIDE_TWO];
//
//     for (int i = 0; i < VALVES_SIDE_TWO; i++) {
//         side_two_durations[i] = valve_durations_side_two[i].as<int>();
//     }
//
//
//     // Update the current trial
//     current_trial = cur_trial;
//
//     // Print side_one_schedule
//     Serial.println("side_one_schedule:");
//     for (JsonVariant value : side_one_schedule) {
//       Serial.println(value.as<int>());
//     }
//
//     // Print side_two_schedule
//     Serial.println("side_two_schedule:");
//     for (JsonVariant value : side_two_schedule) {
//       Serial.println(value.as<int>());
//     }
//
//     // Print current_trial
//     Serial.print("current_trial: ");
//     Serial.println(current_trial);
//
//     // Print valve_durations
//     Serial.println("valve_durations_side_one:");
//     for (JsonVariant value : valve_durations_side_one) {
//       Serial.println(value.as<int>());
//     }
//     Serial.println("valve_durations_side_two:");
//     for (JsonVariant value : valve_durations_side_one) {
//       Serial.println(value.as<int>());
//     }
//
//
//     Serial.println("Data dictionary received and processed.");
// }

void schedule_verification() {
  // echo recieved schedules to python controller, so that it can verify that
  // we received them correctly
  for (int i = 0; i < side_one_sched_vec.size(); i++) {
    Serial.print(side_one_sched_vec.at(i));
  }
  // Serial.println();

  for (int i = 0; i < side_two_sched_vec.size(); i++) {
    Serial.print(side_two_sched_vec.at(i));
  }
  Serial.println();

  // Serial.println("Schedule sent back for verification.");
}
