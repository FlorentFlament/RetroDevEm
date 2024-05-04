import fcntl
import os
import struct

# Constants for the event structure
# https://www.kernel.org/doc/html/latest/input/input.html
# https://docs.python.org/3/library/struct.html
EVENT_FORMAT = 'llHHi' # long, long, uint16_t, uint16_t, uint32_t
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

# Events types
EV_KEY = 1
EV_REL = 2
# Events codes
REL_X = 0
REL_Y = 1
BTN_LEFT = 272
BTN_RIGHT = 273

# USB mouse events location
USB_DEVICE = "/dev/input/event0"

class InputDevice:
    def __init__(self, device="/dev/input/event0"):
        """device the path to the input device, like """
        self.device = open(device, 'rb', buffering=0)
        fd = self.device.fileno()
        flag = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)

    def get_events(self):
        """Process every event in the USB device file"""
        rv = []
        event_data = self.device.read(EVENT_SIZE)
        while event_data:
            rv.append( struct.unpack(EVENT_FORMAT, event_data) )
            event_data = self.device.read(EVENT_SIZE)
        return rv
