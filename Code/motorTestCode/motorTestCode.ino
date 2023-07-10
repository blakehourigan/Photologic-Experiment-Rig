/*
#include <Stepper.h>
#define STEPS 200

Stepper stepper(200, 28, 26);
#define motorInterfaceType 1



void setup() {
  // put your setup code here, to run once:
 Serial.begin(9600);
 stepper.setSpeed(400);
 stepper.step(8960);
 delay(3000);
 stepper.step(-4480);


}

  userInput = int(Serial.read());
  if(userInput != -1){
    stepper.step(userInput);
  }
  Serial.print(userInput);
  

void loop() {
  // put your main code here, to run repeatedly:

}
*/

#include <AccelStepper.h>

// Define stepper motor connections and motor interface type. Motor interface type must be set to 1 when using a driver:
#define dirPin 26  // Direction
#define stepPin 28  // Step

String string;
int val = 0;

// Create a new instance of the AccelStepper class:
AccelStepper stepper = AccelStepper(1, stepPin, dirPin); 

void setup() {
  // Set the maximum speed and acceleration:
  stepper.setMaxSpeed(500);
  stepper.setAcceleration(500);
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
