#!/usr/bin/env python3
import time
from gpiozero import LED
import inputdevice as idev

# Update according to board design
XA = LED(27)
XB = LED(17)
YA = LED(4)
YB = LED(22)
LB = LED(10) # Left mouse button
RB = LED(2) # Right mouse button

# Slow down mouse motion -> Divide mouse speed by MOUSE_SCALE
MOUSE_SCALE = 2

# Mouse is polled at 62.5 Hz (obtained using evtest)
# Atari ST screen vertical freq in 50 Hz
REFRESH_PERIOD = 1 / 80
MAX_TICK_PERIOD = REFRESH_PERIOD / 2
MIN_TICK_PERIOD = 1 / 2000 # 2 KHz
TICK_PERIOD_DECAY = 1.01
STATS_PERIOD = 0.5 # seconds

A_SIGNAL = (0, 1, 1, 0)
B_SIGNAL = (0, 0, 1, 1)

class StMouse:
    def __init__(self):
        self.x_state = 0
        self.y_state = 0
        self.x_delta = 0
        self.y_delta = 0
        self.tick_period = MAX_TICK_PERIOD
        self.worst_delay = 0
        LB.off() # Button not pressed
        RB.off()

    def x_step(self, dir):
        """dir can be 1 for right or -1 for left"""
        self.x_state = (self.x_state + dir) % 4
        if A_SIGNAL[self.x_state]: XA.on()
        else: XA.off()
        if B_SIGNAL[self.x_state]: XB.on()
        else: XB.off()

    def y_step(self, dir):
        self.y_state = (self.y_state + dir) % 4
        if A_SIGNAL[self.y_state]: YB.on()
        else: YB.off()
        if B_SIGNAL[self.y_state]: YA.on()
        else: YA.off()

    def btn_left(self, val):
        if val: LB.on()
        else  : LB.off()

    def btn_right(self, val):
        if val: RB.on()
        else  : RB.off()

    def x_move(self, val):
        self.x_delta += val

    def y_move(self, val):
        self.y_delta += val

    def update_tick_period(self):
        delta_steps = max(abs(self.x_delta), abs(self.y_delta)) / MOUSE_SCALE
        if delta_steps >= 1:
            self.tick_period = min( self.tick_period, REFRESH_PERIOD / delta_steps ) # Only faster
            self.tick_period = max( self.tick_period, MIN_TICK_PERIOD )
            self.tick_period = min( self.tick_period, MAX_TICK_PERIOD )

    def update_worst_delay(self, ev_time):
        delta_steps = max(abs(self.x_delta), abs(self.y_delta)) / MOUSE_SCALE
        if delta_steps >= 1: # We can't tell if we don't have any step in queue
            evt_delay = time.time() - ev_time
            sig_delay = evt_delay + delta_steps * self.tick_period
            self.worst_delay = max(self.worst_delay, sig_delay)

    def decay_tick_period(self):
        delta_steps = max(abs(self.x_delta), abs(self.y_delta)) / MOUSE_SCALE
        if delta_steps < 1:
            self.tick_period = self.tick_period * TICK_PERIOD_DECAY
            self.tick_period = min(self.tick_period, MAX_TICK_PERIOD)

    def get_tick_period(self):
        return self.tick_period

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
        self.decay_tick_period()

    def process_events(self, events):
        for ev_sec, ev_us, ev_type, ev_code, ev_value in events:
            if ev_type == idev.EV_REL:
                if   ev_code == idev.REL_X: self.x_move(ev_value)
                elif ev_code == idev.REL_Y: self.y_move(ev_value)
            elif ev_type == idev.EV_KEY:
                if   ev_code == idev.BTN_LEFT : self.btn_left(ev_value)
                elif ev_code == idev.BTN_RIGHT: self.btn_right(ev_value)
            self.update_tick_period()
            self.update_worst_delay(ev_sec + ev_us*1e-6)

    def display_stats(self):
        tick_us  = int(self.get_tick_period() * 1e6)
        delay_ms = int(self.worst_delay * 1e3)
        stats = f"Tick: {tick_us} us"
        if delay_ms: stats += f" - Delay: {delay_ms} ms"
        self.worst_delay = 0
        print(stats)

def main():
    sm = StMouse()
    dev = idev.InputDevice(blocking=False)

    next_tick = time.monotonic() # time.monotonic is more accurate than time.time
    next_stat = next_tick
    while True:
        # Retrieve every event in the queue
        event_l = []
        event = dev.get_event() # Non blocking
        while event:
            event_l.append(event)
            event = dev.get_event()
        sm.process_events(event_l)

        sm.signals_tick()
        next_tick += sm.get_tick_period()
        # Display some statistics
        if time.monotonic() > next_stat:
            sm.display_stats()
            next_stat += STATS_PERIOD
        try:
            time.sleep( next_tick - time.monotonic() )
        except ValueError:
            pass

if __name__ == "__main__":
    main()
