import fcntl
import os
import struct

# Constants for the event structure
# https://www.kernel.org/doc/html/latest/input/input.html
# https://docs.python.org/3/library/struct.html
EVENT_FORMAT = 'llHHi' # long, long, uint16_t, uint16_t, uint32_t
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

# Obtained using the evtest CLI
# Events types
EV_KEY = 1
EV_REL = 2
EV_ABS = 3
# Events codes
# Mouse events codes
REL_X = 0 # Mouse x move
REL_Y = 1 # Mouse y move
BTN_LEFT = 272 # Mouse left button
BTN_RIGHT = 273 # Mouse right button
# Gamepad events codes
ABS_HAT0X = 16 # Gamepad directional arrows left (-1) right (+1)
ABS_HAT0Y = 17 # Gamepad directional arrows down (-1) up (+1)
BTN_SOUTH = 304 # X button off (-1) on (+1)

# USB mouse events location
USB_DEVICE = "/dev/input/event0"

class InputDevice:
    def __init__(self, device="/dev/input/event0", blocking=True):
        """device the path to the input device."""
        self.device = open(device, 'rb', buffering=0)
        if not blocking:
            fd = self.device.fileno()
            flag = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)

    def get_event(self):
        """Retrieve a single event.  Either blocks until an event is
        available (in blocking mode), or returns None if no event were
        found while file opened in non-blocking mode.

        """
        event_data = self.device.read(EVENT_SIZE)
        if event_data:
            return struct.unpack(EVENT_FORMAT, event_data)
