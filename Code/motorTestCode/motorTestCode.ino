#include <AccelStepper.h>

// Define stepper motor connections and motor interface type. Motor interface type must be set to 1 when using a driver:
#define dirPin 26  // Direction
#define stepPin 28  // Step

String string;
int val = 0;
unsigned long startTime;
unsigned long endTime; 
int finishedFlag; 


// Create a new instance of the AccelStepper class:
AccelStepper stepper = AccelStepper(1, stepPin, dirPin); 

void setup() {
  // Set the maximum speed and acceleration:
  stepper.setMaxSpeed(1800);
  stepper.setAcceleration(1800);
  Serial.begin(9600);


}

void loop() {
  // Set the target position:
     if (Serial.available()) {
       string = Serial.readStringUntil('\n');
       val = string.toInt(); 
       Serial.println(val);
     }
    stepper.moveTo(val);
    
    while (stepper.distanceToGo() != 0) 
    {
    stepper.run();
    }
  }
