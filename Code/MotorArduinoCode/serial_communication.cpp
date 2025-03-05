#include "serial_communication.h"

void SerialCommunication::clear_serial_buffer() {
  while (Serial.available() > 0) {
    // Read and discard the incoming byte
    Serial.read();
  }
}

String SerialCommunication::receive_transmission() {
  String message = "";
  char c;
  // Flag to detect start of message
  bool startDetected = false;

  // Keep reading characters until '>' is encountered
  while (true) {
    if (Serial.available() > 0) {
      c = Serial.read();
      // Check for the end of the message
      if (c == '>') {
        // End of message, exit the loop
        break;
      }
      // Skip adding to message until start character '<' is found
      if (c == '<') {
        // Mark start detected
        startDetected = true;
        // Skip adding the '<' character
        continue;
      }
      if (startDetected) {
        // Add the character to the message string only after
        // '<' is detected
        message += c;
      }
    }
  }
  // Return the complete message read from Serial, excluding the
  // starting character '<'
  return message;
}
