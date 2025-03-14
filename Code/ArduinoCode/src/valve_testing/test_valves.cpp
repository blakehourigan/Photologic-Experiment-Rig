#include "test_valves.h"
#include "../valve_control/valve_control.h"
#include "Arduino.h"
#include "HardwareSerial.h"

/* the best way to do this may be to accept a schedule from controller, and just
 * read from each schedule while theres items left in it if that makes sense
 * like, user can pick, i want to test 1,2, and 5, if for whatever reason they
 * want just those tested. then the program will run through each list until its
 * empty.
 *
 */

TestParams receive_test_params() {
  /* This function receives valve testing parametes such as how many valves will
   * be tested on side one and side two, and how many times each valve will
   * actuate. Once recieved, it echoes these values back to the controller for
   * validation. It returns these values to be used in receive_test_schedules.
   */

  TestParams test_params;

  while (Serial.available() < 4) {
  }

  test_params.num_valves_side_one = Serial.read();
  test_params.num_valves_side_two = Serial.read();

  uint16_t byte0 = Serial.read();
  uint16_t byte1 = Serial.read();

  test_params.max_test_actuations = byte0 | (byte1 << 8);

  Serial.write((uint8_t *)&test_params.num_valves_side_one,
               sizeof(test_params.num_valves_side_one));
  Serial.write((uint8_t *)&test_params.num_valves_side_two,
               sizeof(test_params.num_valves_side_two));
  Serial.write((uint8_t *)&test_params.max_test_actuations,
               sizeof(test_params.max_test_actuations));
  Serial.flush();

  return test_params;
}

void schedule_verification(TestParams test_params) {
  ExpScheduleArray side_one_arr = test_params.side_one_sched;
  ExpScheduleArray side_two_arr = test_params.side_two_sched;

  // echo recieved schedules to python controller, so that it can verify
  // that we received them correctly
  for (int i = 0; i < side_one_arr.len; i++) {
    Serial.write(side_one_arr.schedule[i]);
  }

  for (int i = 0; i < side_two_arr.len; i++) {
    Serial.write(side_two_arr.schedule[i]);
  }
  // force all the data out
  Serial.flush();

  // Serial.println("Schedule sent back for verification.");
}

TestParams receive_test_schedules() {
  /* receive the sched (maybe or maybe not using the exp_init method),
   * durations, and NUMBER OF TESTS iterations for each valve.
   */

  // we should be able to just recieve the full durations in main and just use
  // the ones we need recieved below, so this we will do first

  // recieve 4 bytes. these bytes will be LEN_VALVE_SCHED_1, LEN_VALVE_SCHED_2,
  // and num_iterations respectively

  TestParams test_params = receive_test_params();

  ExpScheduleArray side_one_arr;
  ExpScheduleArray side_two_arr;

  // if we have any serial bytes available, read one byte in and
  // say that this byte represents which valve to select for this trial
  uint8_t total_bytes =
      test_params.num_valves_side_one + test_params.num_valves_side_two;

  while (Serial.available() < total_bytes) {
  }

  for (int i = 0; i < test_params.num_valves_side_one; i++) {
    side_one_arr.append(Serial.read());
  }

  for (int i = 0; i < test_params.num_valves_side_two; i++) {
    side_two_arr.append(Serial.read());
  }
  test_params.side_one_sched = side_one_arr;
  test_params.side_two_sched = side_two_arr;

  schedule_verification(test_params);

  return test_params;

  // wait until LEN_VALVE_SCHED_1 LEN_VALVE_SCHED_2 bytes are avail, because
  // these will be uint8_t, read LEN_VALVE_SCHED_1 bytes into the first sched
  // vec, then read LEN_VALVE_SCHED_2 bytes into second vec
}

void run_valve_test(DurationsArray side_one, DurationsArray side_two) {
  // const defined in exp_init.h, max len of 8 per side

  TestParams test_params = receive_test_schedules();

  ExpScheduleArray side_one_sched = test_params.side_one_sched;
  ExpScheduleArray side_two_sched = test_params.side_two_sched;

  bool testing = false;

  // start each schedule position at 0
  uint8_t sched_location = 0;

  uint16_t valve_openings = 0;

  // wait for the start signal
  while (Serial.available() < 1) {
  }

  bool start_command = Serial.read();

  if (start_command == true) {
    testing = true;
  } else if (start_command == false) {
    return;
  }

  while (testing) {
    if (valve_openings <= test_params.max_test_actuations) {
      if (Serial.available() > 0) {
        // if we send the abort signal, handle it immediately.
        bool command = Serial.read();
        if (command == 0) {
          // abort
          return;
        }
      }
      if (sched_location < side_one_sched.len) {
        uint8_t valve = side_one_sched.schedule[sched_location];

        open_single_valve(&PORTA, valve);

        unsigned long delay_time = side_one.durations[valve];

        uint16_t clean_delay = delay_time / 1000;
        uint16_t remainder_delay = delay_time % 1000;

        delay(clean_delay);
        delayMicroseconds(remainder_delay);

        close_single_valve(&PORTA, valve);
      } else {
        delay(25);
      }
      if (sched_location < side_two_sched.len) {
        uint8_t valve = side_two_sched.schedule[sched_location] -
                        ((MAX_VALVES_PER_SIDE / 2));

        open_single_valve(&PORTC, valve);

        unsigned long delay_time = side_two.durations[valve];

        uint16_t clean_delay = delay_time / 1000;
        uint16_t remainder_delay = delay_time % 1000;

        delay(clean_delay);
        delayMicroseconds(remainder_delay);
        close_single_valve(&PORTC, valve);
      } else {
        delay(25);
      }
      valve_openings++;
    } else {
      valve_openings = 0;
      sched_location++;

      if (sched_location >= side_one_sched.len &&
          sched_location >= side_two_sched.len) {
        testing = false;
        // send 0 indicating no more valves remaining.
        // send sched location-1 to maintain data format of 2 bytes per tx
        Serial.write(0);
        Serial.write(sched_location - 1);
        Serial.flush();
        // testing complete, exit function
        return;
      }

      // send 1 indicating more valves remain.
      // send sched location -1 to tell controller which pair we tested.
      Serial.write(1);
      Serial.write(sched_location - 1);
      Serial.flush();
      while (Serial.available() == 0) {
      }

      // there are only two options at this point, continue or abort
      bool command = Serial.read();

      if (command == 1) {
        // continue to the next pair
        continue;
      } else if (command == 0) {
        // abort
        return;
      }
    }
  }
}
