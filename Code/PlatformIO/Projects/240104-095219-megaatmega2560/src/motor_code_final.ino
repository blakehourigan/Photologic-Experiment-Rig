#include <AccelStepper.h>

#define dir_pin 26
#define step_pin 28

int side_one_solenoids[] = {30, 31, 32, 33, 34, 35, 36, 37};
int side_two_solenoids[] = {38, 39, 40, 41, 42, 43, 44, 45};

unsigned long start_time;
unsigned long end_time;
unsigned long duration;
unsigned long valve_open_time_d, valve_open_time_c, open_start, close_time;

int side_one_lick_duration = 37500; // 37.5 milliseconds vale 1 
int side_two_lick_duration = 24125; // 24.125 milliseconds valve 2  

AccelStepper stepper = AccelStepper(1, step_pin, dir_pin);

void toggle_solenoid(int solenoid_pin) 
{
  int pin_state = digitalRead(solenoid_pin);
  digitalWrite(solenoid_pin, pin_state == HIGH ? LOW : HIGH);
}

void lick_handler(int solenoid_value, int* solenoids, String side)
{
  int duration = 0;

  if (side == "SIDE_ONE"){
    duration = side_one_lick_duration; // gives us the duration of the lick in microseconds
  }else if (side == "SIDE_TWO"){
    duration = side_two_lick_duration;
  }
  int quotient = duration / 10000; // delayMicroseconds only allows for values up to 16383, we use multiple instances of 
  // 10000 to avoid overflow

  int remaining_delay = duration - (quotient * 10000);  
  PORTD |= (1 << PD7); 

  toggle_solenoid(solenoids[solenoid_value - 1]);

  for (int i = 0; i < quotient; i++)
  {
    delayMicroseconds(10000);
  }
    delayMicroseconds(remaining_delay); // we add the remaining delay to the end of the loop to ensure the total duration is correct
    toggle_solenoid(solenoids[solenoid_value - 1]);
    PORTD &= ~(1 << PD7);

    delay(50);
}

void setup() 
{
  stepper.setMaxSpeed(1800);
  stepper.setAcceleration(1800);
  Serial.begin(115200);
  for (int i = 0; i < 8; i++) {
    pinMode(side_one_solenoids[i], OUTPUT);
    pinMode(side_two_solenoids[i], OUTPUT);
  }
  DDRC |= (1 << PC7); // Set pin 30 as an output
  DDRD |= (1 << PD7); // Set pin 30 as an output
}

void test_valve_operation() 
{
    // Set pin 38 as an output
    DDRD |= (1 << PD7);

    // Open the valve
    PORTD |= (1 << PD7); 
    unsigned long start_time = millis();

    // Wait for 3 minutes (180000 milliseconds)
    while(millis() - start_time < 150000) {
        // Keep the loop running for 3 minutes
    }

    // Close the valve
    PORTD &= ~(1 << PD7);
    unsigned long end_time = millis();

    // Calculate duration
    unsigned long duration = end_time - start_time;
  
    // Print the duration
    Serial.print("Time valve was open: ");
    Serial.print(duration);
    Serial.println(" milliseconds");
}

// In your main loop or setup, call this function
// test_valve_operation();

void loop() 
{
  if (Serial.available()) 
  {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "SIDE_ONE" || command == "SIDE_TWO") {
      int solenoid_value = Serial.readStringUntil('\n').toInt();

      int* solenoids;
      String side;

      if (command == "SIDE_ONE"){
        solenoids = side_one_solenoids;
        side = "SIDE_ONE";
        lick_handler(solenoid_value, solenoids, side);
      }else if (command == "SIDE_TWO"){
        solenoids = side_two_solenoids;
        side = "SIDE_TWO";
        lick_handler(solenoid_value, solenoids, side);
      }
    } else if (command == "reset") {
        asm volatile ("jmp 0");
    } else if (command == "UP") {
        stepper.moveTo(0);
    } else if (command == "DOWN") {
        stepper.moveTo(-6400);
    } else if (command == "WHO_ARE_YOU") {
        Serial.println("MOTOR");
    } else if (command == "test_open_close"){
        DDRC |= (1 << PC7); // Set pin 30 as an output
        DDRD |= (1 << PD7); // Set pin 30 as an output

        for(int i = 0; i < 1000; i++)
        {
          Serial.println(i);
          open_start = millis();
          PORTD |= (1 << PD7); // Set pin 38 to HIGH (Valve 1)
          // max value of delayMicroseconds is 16383, using smaller multiples of 10000 to avoid overflow
          delayMicroseconds(10000);
          delayMicroseconds(10000);
          delayMicroseconds(10000);
          delayMicroseconds(7500);
          PORTD &= ~(1 << PD7); // Set pin 38 to LOW (close)
          delay(25);
          close_time = millis();
          valve_open_time_d += (close_time - open_start);

          open_start = millis();
          
          PORTC |= (1 << PC7); // Set pin 30 to HIGH (valve 2) 
          delayMicroseconds(10000);
          delayMicroseconds(10000);
          delayMicroseconds(4125);
          PORTC &= ~(1 << PC7); // Set pin 30 to low (close)
          delay(25);
          close_time = millis();
          valve_open_time_c += (close_time - open_start);

          delay(100);
        } 
    Serial.print("Valve one opened for: ");
    Serial.print(valve_open_time_d);
    Serial.println(" milliseconds.");
    Serial.print("Valve two opened for: ");
    Serial.print(valve_open_time_c);
    Serial.println(" milliseconds.");

    } else if (command =="test_flow_rate"){
        test_valve_operation();
    } else if (command == "open_all"){
        for(int i = 0; i < 8; i++)
        {
          PORTD |= (1 << PD7); // Set pin 38 to HIGH (Valve 1)
          PORTC |= (1 << PC7); // Set pin 30 to HIGH (valve 2) 
          delay(100);
        }
    } else if (command == "close_all"){
        for(int i = 0; i < 8; i++)
        {
          PORTD &= ~(1 << PD7); // Set pin 38 to LOW (close)
          PORTC &= ~(1 << PC7); // Set pin 30 to low (close)
          delay(100);
        }
    }
      
  }
  stepper.run();
}