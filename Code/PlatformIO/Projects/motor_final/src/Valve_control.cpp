#include "valve_control.h"

/* toggle the solenoid valve for the side that was licked by overwriting the register value of 0
   on the corresponding side with the value held at the position of the current trial index in the 
   corresponding sides schedule list. 
*/
void valve_control::toggle_solenoid(int side, int *side_one_schedule, int *side_two_schedule, int current_trial, bool testing, int valve) {
  int porta_value = 0;
  int portc_value = 0; 
  Serial.println("testing");
  if(testing && side == 0){
    porta_value = 1 << valve;
    
    PORTA = porta_value;
    Serial.print("Testing valve on side one: "); Serial.println(valve);
  }
  else if(testing && side == 1){
    portc_value = 1 << valve;
    PORTC = portc_value;
    Serial.print("Testing valve on side two: "); Serial.println(valve);
  }
  else{
    porta_value = side_one_schedule[current_trial];
    portc_value = side_two_schedule[current_trial];

    if (side == 0) {
      PORTA = porta_value;
      Serial.print("Toggled solenoid on side one with value: "); Serial.println(porta_value, BIN);
    } else if (side == 1) {
      PORTC = portc_value;
      Serial.print("Toggled solenoid on side two with value: "); Serial.println(portc_value, BIN);
    }
  }
}

void valve_control::untoggle_solenoids() 
{
    PORTA = 0 ;
    PORTC = 0 ;
    Serial.println("Solenoids untoggled.");
}

void valve_control::lick_handler(int valve_side, int *side_one_schedule, int *side_two_schedule, unsigned long *side_one_durations, unsigned long *side_two_durations,int current_trial, bool testing, int valve_number) {
  noInterrupts();

  long int valve_duration;

  if(valve_side == 0){
    valve_duration = side_one_durations[valve_number]; 
  }
  else if(valve_side == 1){
    valve_duration = side_two_durations[valve_number];
  }

  Serial.print("Read valve duration: "); Serial.println(valve_duration);

  int quotient = valve_duration / 10000;
  int remaining_delay = valve_duration - (quotient * 10000);

  if (testing){
    Serial.println("testing in da lick handler bru");
    toggle_solenoid(valve_side, side_one_schedule, side_two_schedule, current_trial, true, valve_number);
  }
  else{
    toggle_solenoid(valve_side, side_one_schedule, side_two_schedule, current_trial);
  }

  for (int i = 0; i < quotient; i++) {
    delayMicroseconds(10000);
  }

  delayMicroseconds(remaining_delay);
  untoggle_solenoids();

  interrupts();
}

