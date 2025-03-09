#include "test_valves.h"
#include "../valve_control/valve_control.h"

const uint16_t NUMBER_OF_TESTS = 1000;

/* the best way to do this may be to accept a schedule from controller, and just
 * read from each schedule while theres items left in it if that makes sense
 * like, user can pick, i want to test 1,2, and 5, if for whatever reason they
 * want just those tested. then the program will run through each list until its
 * empty.
 *
 *
 * also, num iterations should be default but variable from the controller.
 */

void recieve_test_params() {
  /* receive the sched (maybe or maybe not using the exp_init method),
   * durations, and NUMBER OF TESTS iterations for each valve.
   */
}

void test_volume(char number_of_valves) {
  // convert char to int
  uint8_t num_valves = number_of_valves - '0';

  uint8_t total_iterations = num_valves / 2;

  /*
  for (int i = 0; i < sched_one.size(); i++) {
    for (int j = 0; j < NUMBER_OF_TESTS; j++) {
      open_valve_testing(&PORTA, i);

      open_valve_testing(p, );
    }
  }
  etc, etc
  */

  // i is the current valve number on either side
  for (int i = 0; i < total_iterations; i++) {
    Serial.print("Testing valve pair: ");
    Serial.println(i + 1);

    for (int j = 0; j < NUMBER_OF_TESTS; j++) {
      open_valve_testing(&PORTA, i);

      open_valve_testing(p, );
    }

    Serial.println("FINISHED PAIR");

    String command = "\0";

    while (true) {
      if (Serial.available() > 0) {
        Serial.readLineUntil('\n');
      }
    }
    if (command.equals("continue")) {
      break;
    }
  }

  Serial.println("TESTING COMPLETE");
}
