#!/usr/bin/env python3

import time
import struct
import fcntl
import os

from gpiozero import LED

# Update according to board design
XA = LED(2)
XB = LED(3)
YA = LED(17) # YA & YB are in reverse order compared to Atari ST internals
YB = LED(4)
LB = LED(27)
RB = LED(22)

# USB mouse events location
MOUSE_EVENTS = "/dev/input/event0" # Mouse events

# Slow down mouse motion -> Divide mouse speed by MOUSE_SCALE
MOUSE_SCALE = 2

REFRESH_PERIOD = 1 / 70 # Mouse is polled at 62.5 Hz (obtained using evtest)
MAX_TICK_PERIOD = REFRESH_PERIOD / 2
MIN_TICK_PERIOD = 1 / 2000 # 2 KHz
TICK_PERIOD_DECAY = 1.01

A_SIGNAL = (0, 1, 1, 0)
B_SIGNAL = (0, 0, 1, 1)

# Constants for the event structure
# https://www.kernel.org/doc/html/latest/input/input.html
# https://docs.python.org/3/library/struct.html
EVENT_FORMAT = 'llHHi'  # long long, uint16_t, uint16_t, uint32_t
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

# Events types
EV_KEY = 1
EV_REL = 2
# Events codes
REL_X = 0
REL_Y = 1
BTN_LEFT = 272
BTN_RIGHT = 273

class StMouse:
        def __init__(self):
                self.x_state = 0
                self.y_state = 0
                self.x_delta = 0
                self.y_delta = 0
                self.tick_period = MAX_TICK_PERIOD
                LB.on()
                RB.on()

        def x_step(self, dir):
                """dir can be 1 for right or -1 for left"""
                self.x_state = (self.x_state + dir) % 4
                if A_SIGNAL[self.x_state]: XA.on()
                else: XA.off()
                if B_SIGNAL[self.x_state]: XB.on()
                else: XB.off()

        def y_step(self, dir):
                self.y_state = (self.y_state + dir) % 4
                if A_SIGNAL[self.y_state]: YA.on()
                else: YA.off()
                if B_SIGNAL[self.y_state]: YB.on()
                else: YB.off()

        def btn_left(self, val):
                #print(f"btn_left: {val}")
                if val: LB.off()
                else  : LB.on()

        def btn_right(self, val):
                #print(f"btn_right: {val}")
                if val: RB.off()
                else  : RB.on()
                
        def x_move(self, val):
                #print(f"Val: {val} - Tick {int(self.get_tick_period() * 1e6)} - Remaining x_delta: {self.x_delta}")
                self.x_delta += val

        def y_move(self, val):
                #print(f"Val: {val} - Tick {int(self.get_tick_period() * 1e6)} - Remaining y_delta: {self.y_delta}")
                self.y_delta += val

        def signals_tick(self):
                # Move mouse pointer
                if abs(self.x_delta) >= MOUSE_SCALE:
                        # increment by (+/-) MOUSE_SCALE
                        inc = MOUSE_SCALE * self.x_delta // abs(self.x_delta)
                        self.x_delta -= inc # Works for positive and negative alike
                        self.x_step(inc // MOUSE_SCALE) # Step is by +/- 1
                if abs(self.y_delta) >= MOUSE_SCALE:
                        inc = MOUSE_SCALE * self.y_delta // abs(self.y_delta)
                        self.y_delta -= inc
                        self.y_step(inc // MOUSE_SCALE)

        def update_tick_period(self):
                delta_steps = max(abs(self.x_delta), abs(self.y_delta)) / MOUSE_SCALE
                if delta_steps >= 1:
                        self.tick_period = min(self.tick_period, REFRESH_PERIOD/delta_steps)
                        self.tick_period = max(self.tick_period, MIN_TICK_PERIOD)
                else:
                        self.tick_period = self.tick_period * TICK_PERIOD_DECAY
                        self.tick_period = min(self.tick_period, MAX_TICK_PERIOD)

        def get_tick_period(self):
                return self.tick_period
                

class UsbMouse:
        def __init__(self, device):
                self.device = open(device, 'rb', buffering=0)
                fd = self.device.fileno()
                flag = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)

        def process_events(self, st_mouse):
                """Process every event in the USB device file"""
                event_data = self.device.read(EVENT_SIZE)
                while event_data:
                        event = struct.unpack(EVENT_FORMAT, event_data)
                        #print(f"Time: {event[0]}.{event[1]}, Type: {event[2]}, Code: {event[3]}, Value: {event[4]}")
                        _, _, ev_type, ev_code, ev_value = event
                        if ev_type == EV_REL:
                                if   ev_code == REL_X: st_mouse.x_move(ev_value)
                                elif ev_code == REL_Y: st_mouse.y_move(ev_value)
                        elif ev_type == EV_KEY:
                                if   ev_code == BTN_LEFT : st_mouse.btn_left(ev_value)
                                elif ev_code == BTN_RIGHT: st_mouse.btn_right(ev_value)
                        event_data = self.device.read(EVENT_SIZE)


def main():
        sm = StMouse()
        um = UsbMouse(MOUSE_EVENTS)

        next_tick = time.monotonic()
        while True:
                um.process_events(sm)
                sm.signals_tick()
                sm.update_tick_period()
                next_tick += sm.get_tick_period()
                try:
                        time.sleep( next_tick - time.monotonic() )
                except ValueError:
                        pass

if __name__ == "__main__":
        main()
