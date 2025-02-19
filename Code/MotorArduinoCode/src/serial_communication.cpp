#include "serial_communication.h"

void SerialCommunication::clear_serial_buffer() 
{
  while (Serial.available() > 0) {
    Serial.read(); // Read and discard the incoming byte
  }
}

String SerialCommunication::receive_transmission()
{
    String message = "";
    char inChar;
    bool startDetected = false; // Flag to detect start of message
    // Keep reading characters until '>' is encountered
    while (true) {
        if (Serial.available() > 0) {
            inChar = Serial.read();
            // Check for the end of the message
            if (inChar == '>') {
                break; // End of message, exit the loop
            }
            // Skip adding to message until start character '<' is found
            if (inChar == '<') {
                startDetected = true; // Mark start detected
                continue; // Skip adding the '<' character
            }
            if (startDetected) {
                message += inChar; // Add the character to the message string only after '<' is detected
            }
        }
    }
    return message; // Return the complete message read from Serial, excluding the starting character '<'
}