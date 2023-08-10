#include <AccelStepper.h>

// Define stepper motor connections and motor interface type. Motor interface type must be set to 1 when using a driver:
#define dirPin 26  // Direction pin
#define stepPin 28  // Step pin 
#define sideOneSolenoid1 30
#define sideOneSolenoid2 31
#define sideOneSolenoid3 32
#define sideOneSolenoid4 33
#define sideOneSolenoid5 34
#define sideOneSolenoid6 35
#define sideOneSolenoid7 36
#define sideOneSolenoid8 37
#define sideTwoSolenoid1 38
#define sideTwoSolenoid2 39
#define sideTwoSolenoid3 40
#define sideTwoSolenoid4 41
#define sideTwoSolenoid5 42
#define sideTwoSolenoid6 43
#define sideTwoSolenoid7 44
#define sideTwoSolenoid8 45


String string;
int val = 0;
unsigned long startTime;
unsigned long endTime; 
int finishedFlag; 
int pinState;

bool readSideOneValue = false; // Flag to indicate if the next line should be read
bool readSideTwoValue = false;
String sideOneValue; // Variable to store the value for "SIDE_ONE"
String sideTwoValue;

// Create a new instance of the AccelStepper class:
AccelStepper stepper = AccelStepper(1, stepPin, dirPin); 

void setup() 
{
  // Set the maximum speed and acceleration:
  stepper.setMaxSpeed(1800);
  stepper.setAcceleration(1800);
  Serial.begin(9600);
  pinMode(sideOneSolenoid1, OUTPUT);
  pinMode(sideOneSolenoid2, OUTPUT);
  pinMode(sideOneSolenoid3, OUTPUT);
  pinMode(sideOneSolenoid4, OUTPUT);
  pinMode(sideOneSolenoid5, OUTPUT);
  pinMode(sideOneSolenoid6, OUTPUT);
  pinMode(sideOneSolenoid7, OUTPUT);
  pinMode(sideOneSolenoid8, OUTPUT);
  pinMode(sideTwoSolenoid1, OUTPUT);
  pinMode(sideTwoSolenoid2, OUTPUT);
  pinMode(sideTwoSolenoid3, OUTPUT);
  pinMode(sideTwoSolenoid4, OUTPUT);
  pinMode(sideTwoSolenoid5, OUTPUT);
  pinMode(sideTwoSolenoid6, OUTPUT);
  pinMode(sideTwoSolenoid7, OUTPUT);
  pinMode(sideTwoSolenoid8, OUTPUT);

}

void loop() 
{
  if (Serial.available()) 
  {
    String command = Serial.readStringUntil('\n');
    command.trim();  // Remove any leading/trailing whitespace

    if (readSideOneValue)
    {
      sideOneValue = command; // Store the value for "SIDE_ONE"
      readSideOneValue = false; // Reset the flag
      switch(sideOneValue.toInt())
      {
        case 1:
          pinState = digitalRead(sideOneSolenoid1);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid1, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid1, HIGH);
          }
        break; 
        case 2:
          pinState = digitalRead(sideOneSolenoid2);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid2, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid2, HIGH);
          }
        break;
        case 3:
          pinState = digitalRead(sideOneSolenoid3);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid3, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid3, HIGH);
          }
        break; 
        case 4:
          pinState = digitalRead(sideOneSolenoid4);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid4, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid4, HIGH);
          }
        break; 
        case 5:
          pinState = digitalRead(sideOneSolenoid5);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid5, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid5, HIGH);
          }
        break; 
        case 6:
          pinState = digitalRead(sideOneSolenoid6);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid6, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid6, HIGH);
          }
        break; 
        case 7:
          pinState = digitalRead(sideOneSolenoid7);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid7, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid7, HIGH);
          }
        break;
        case 8:
          pinState = digitalRead(sideOneSolenoid8);
          if(pinState == HIGH)
          {
            digitalWrite(sideOneSolenoid8, LOW);
          }
          else
          {
            digitalWrite(sideOneSolenoid8, HIGH);
          }
        break;    

      }
    }
    else if (readSideTwoValue)
    {
        sideTwoValue = command; // Store the value for "SIDE_ONE"
        readSideTwoValue = false; // Reset the flag
        switch(sideOneValue.toInt())
        {
          case 1:
            pinState = digitalRead(sideTwoSolenoid1);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid1, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid1, HIGH);
            }
          break; 
          case 2:
            pinState = digitalRead(sideTwoSolenoid2);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid2, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid2, HIGH);
            }
          break;
          case 3:
            pinState = digitalRead(sideTwoSolenoid3);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid3, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid3, HIGH);
            }
          break; 
          case 4:
            pinState = digitalRead(sideTwoSolenoid4);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid4, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid4, HIGH);
            }
          break; 
          case 5:
            pinState = digitalRead(sideTwoSolenoid5);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid5, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid5, HIGH);
            }
          break; 
          case 6:
            pinState = digitalRead(sideTwoSolenoid6);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid6, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid6, HIGH);
            }
          break; 
          case 7:
            pinState = digitalRead(sideTwoSolenoid7);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid7, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid7, HIGH);
            }
          break;
          case 8:
            pinState = digitalRead(sideTwoSolenoid8);
            if(pinState == HIGH)
            {
              digitalWrite(sideTwoSolenoid8, LOW);
            }
            else
            {
              digitalWrite(sideTwoSolenoid8, HIGH);
            }
          break;    

        }

    }
  

    if(command == "reset")
    {
      asm volatile ("jmp 0");  // Jump to the start of the program
    }
    else if(command == "UP")
    {
      stepper.moveTo(0);
    }

    else if(command == "DOWN")
    {
      stepper.moveTo(6400);
    }
  
    else if(command == "SIDE_ONE")
    {
      readSideOneValue = true;
    }
    else if(command == "SIDE_TWO")
    {
      readSideTwoValue = true;
    }

  }
  stepper.run();
}


