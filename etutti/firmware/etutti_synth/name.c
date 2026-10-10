// Gives the Teensy the USB device name "eTutti" instead of the default
// "Teensy MIDI", so the web page (and any DAW) lists it by name.
// Teensyduino picks this file up automatically when it sits in the
// sketch folder. Windows may keep showing the old name until the device
// is removed in Device Manager and plugged in again.

#include "usb_names.h"

#define MIDI_NAME   {'e','T','u','t','t','i'}
#define MIDI_NAME_LEN  6

struct usb_string_descriptor_struct usb_string_product_name = {
  2 + MIDI_NAME_LEN * 2,
  3,
  MIDI_NAME
};
