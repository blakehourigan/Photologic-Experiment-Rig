#include <AccelStepper.h>

#define dirPin 26
#define stepPin 28

int sideOneSolenoids[] = {30, 31, 32, 33, 34, 35, 36, 37};
int sideTwoSolenoids[] = {38, 39, 40, 41, 42, 43, 44, 45};

unsigned long startTime;
unsigned long endTime;
unsigned long duration;
unsigned long valveOpenTimeD, valveOpenTimeC, open_start, close_time;

AccelStepper stepper = AccelStepper(1, stepPin, dirPin);

void toggleSolenoid(int solenoidPin) 
{
  int pinState = digitalRead(solenoidPin);
  digitalWrite(solenoidPin, pinState == HIGH ? LOW : HIGH);
}

void setup() 
{
  stepper.setMaxSpeed(1800);
  stepper.setAcceleration(1800);
  Serial.begin(115200);
  for (int i = 0; i < 8; i++) {
    pinMode(sideOneSolenoids[i], OUTPUT);
    pinMode(sideTwoSolenoids[i], OUTPUT);
  }
}

void testValveOperation() 
{
    // Set pin 38 as an output
    DDRD |= (1 << PD7);

    // DDRC |= (1 << PC7); // Set pin 30 as an output
    // PORTC |= (1 << PC7); // Set pin 30 to HIGH

    // Open the valve
    PORTD |= (1 << PD7); 
    unsigned long startTime = millis();

    // Wait for 3 minutes (180000 milliseconds)
    while(millis() - startTime < 150000) {
        // Keep the loop running for 3 minutes
    }

    // Close the valve
    PORTD &= ~(1 << PD7);
    unsigned long endTime = millis();

    // Calculate duration
    unsigned long duration = endTime - startTime;
  
    // Print the duration
    Serial.print("Time valve was open: ");
    Serial.print(duration);
    Serial.println(" milliseconds");
}


// In your main loop or setup, call this function
// testValveOperation();


void loop() 
{
  if (Serial.available()) 
  {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "SIDE_ONE" || command == "SIDE_TWO") {
      int solenoidValue = Serial.readStringUntil('\n').toInt();
      int* solenoids = command == "SIDE_ONE" ? sideOneSolenoids : sideTwoSolenoids;
      toggleSolenoid(solenoids[solenoidValue - 1]);
    } else if (command == "reset") {
        asm volatile ("jmp 0");
    } else if (command == "UP") {
        stepper.moveTo(0);
    } else if (command == "DOWN") {
        stepper.moveTo(6400);
    } else if (command == "WHO_ARE_YOU") {
        Serial.println("MOTOR");
    } else if (command == "test"){
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
          valveOpenTimeD += (close_time - open_start);

          open_start = millis();
          
          PORTC |= (1 << PC7); // Set pin 30 to HIGH (valve 2) 
          delayMicroseconds(10000);
          delayMicroseconds(10000);
          delayMicroseconds(4125);
          PORTC &= ~(1 << PC7); // Set pin 30 to low (close)
          delay(25);
          close_time = millis();
          valveOpenTimeC += (close_time - open_start);

          delay(100);
        } 
    Serial.print("Valve one opened for: ");
    Serial.print(valveOpenTimeD);
    Serial.println(" milliseconds.");
    Serial.print("Valve two opened for: ");
    Serial.print(valveOpenTimeC);
    Serial.println(" milliseconds.");

    } else if (command =="OPEN"){
        testValveOperation();
    } 
      
  }
  stepper.run();
}