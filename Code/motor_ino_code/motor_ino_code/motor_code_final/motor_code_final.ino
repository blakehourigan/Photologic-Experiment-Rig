#include <AccelStepper.h>

#define dirPin 26
#define stepPin 28

int sideOneSolenoids[] = {30, 31, 32, 33, 34, 35, 36, 37};
int sideTwoSolenoids[] = {38, 39, 40, 41, 42, 43, 44, 45};

AccelStepper stepper = AccelStepper(1, stepPin, dirPin);

void toggleSolenoid(int solenoidPin) {
  int pinState = digitalRead(solenoidPin);
  digitalWrite(solenoidPin, pinState == HIGH ? LOW : HIGH);
}

void setup() {
  stepper.setMaxSpeed(1800);
  stepper.setAcceleration(1800);
  Serial.begin(9600);
  for (int i = 0; i < 8; i++) {
    pinMode(sideOneSolenoids[i], OUTPUT);
    pinMode(sideTwoSolenoids[i], OUTPUT);
  }
}

void loop() {
  if (Serial.available()) {
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
    }
  }
  stepper.run();
}
