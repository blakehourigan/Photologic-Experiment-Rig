#ifndef SERIAL_COMMUNICATION_H
#define SERIAL_COMMUNICATION_H

#include <Arduino.h>

class SerialCommunication {
public:
    static void clear_serial_buffer();
    static String receive_transmission();

private:
    // Add any private member functions or variables here
};

#endif

