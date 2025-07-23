// —————— Counters & state ——————
int port_1_val = 0;
int port_2_val = 0;

bool port_1_prev_state = false;
bool port_2_prev_state = false;

bool port_1_state = false;
bool port_2_state = false;




void setup() {
  Serial.begin(115200);

  // QT breakout pins (using PORTB bits 0 and 2)
  DDRB &= ~(1<<PB0); // digital 53
  DDRB &= ~(1<<PB2); // digital 51


  DDRG &= ~(1 << PG2); // digital 39, enable signal. will not count unless this goes high.
  DDRG &= ~(1 << PG0); // digital 41, reset signal. will print currently held values of both pins when high. 
}

void loop() {
  static int current_trial_num = 1;

  static unsigned long last_poll = 0;
  static unsigned long last_lick_end = 0;
  
  static unsigned long last_reset = 0;
  

  static unsigned long side_1_start = 0;
  static unsigned long side_1_end = 0;
  static unsigned long side_2_start = 0;
  static unsigned long side_2_end = 0;

  static unsigned long low_start_time = 0;
  static bool port_1_falling_edge = false;
  static bool port_2_falling_edge = false;

  // utilized for a sample lick. we only move on from a lick once both valve close time AND 
  // lick finish time have been marked.
  bool accept_licks = (PING & (1 << PG2)) != 0;
  
  // only reset when PG0 is high, ensure that we don't reset too often.
  bool reset_trials = (PING & (1 << PG0)) != 0;
  
  if(reset_trials && ((millis() - last_reset) > 30)){
    Serial.print("\n|===============================================|\n");
    Serial.print("\t\tFinished Trial Number -> ");
    Serial.print(current_trial_num);
    Serial.print("\n");
    Serial.print("\t\tSide one licks: ");
    Serial.println(port_1_val);
    
    Serial.print("\t\tSide two licks: ");
    Serial.println(port_2_val);
    Serial.print("\n|===============================================|");

    // reset counts
    port_1_val = 0;
    port_2_val = 0;

    current_trial_num++;

    last_reset = millis();
  }

  static bool handling_lick = false;

  // Read current port state as booleans
  if((millis() - last_poll) > 1){
    // update prev state for next loop
    port_1_prev_state = port_1_state;
    port_2_prev_state = port_2_state;

    port_1_state = (PINB & (1 << PINB0)) != 0;
    port_2_state = (PINB & (1 << PINB2)) != 0;

    last_poll = millis();

  }


  if (accept_licks && (!handling_lick)){
    // reject licks if that start before 90 millis-seconds after last lick has ended.
    if(millis() - last_lick_end > 60){
      if (port_1_state && !port_1_prev_state) {
        // only increment once per touch
        handling_lick = true;
        side_1_start = millis();
      }

      if (port_2_state && !port_2_prev_state) {
        handling_lick = true;
        side_2_start = millis();
      }
    }
  }else if(handling_lick && !(reset_trials)){
    // ——— Port 1: rising‐edge detection ———
    if (!(port_1_state) && port_1_prev_state) {
      low_start_time = millis();
      port_1_falling_edge = true;

    }
    // ——— Port 2: same thing ———
    else if (!(port_2_state) && port_2_prev_state) {
      low_start_time = millis();
      port_2_falling_edge = true;
    }

    if(port_1_falling_edge && !port_1_state){
      if(millis() - low_start_time > 1){   
          port_1_val++;
          side_1_end = millis();

          Serial.print("Lick on port 1, current value -> ");
          Serial.print(port_1_val);
          Serial.print(" | duration -> ");
          Serial.println(side_1_end - side_1_start);

        handling_lick = false;
        last_lick_end= millis();
        port_1_falling_edge = false;

      }

    }
    if(port_2_falling_edge && !port_2_state){
      if(millis() - low_start_time > 1){      
          port_2_val++;
          side_1_end = millis();

          Serial.print("Lick on port 2, current value -> ");
          Serial.print(port_2_val);
          Serial.print(" | duration -> ");
          Serial.println(side_2_end - side_2_start);

        handling_lick = false;
        last_lick_end= millis();
        port_2_falling_edge = false;
      }
    }
  }else{
    // don't count lick that didn't complete before trial end. 
    handling_lick = false;

  }
}


