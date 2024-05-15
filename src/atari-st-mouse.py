#!/usr/bin/env python3
import time
import click
from gpiozero import LED
import inputdevice as idev

BOARDS_CONFIG = {
    "v2.0": {
        "XA" : 4,
        "XB" : 17,
        "YA" : 3,
        "YB" : 22,
        "LB" : 27, # Left mouse button
        "RB" : 10, # Right mouse button
    },
    "v2.1": {
	"XA" : 27,
	"XB" : 22,
	"YA" : 17,
	"YB" : 4,
	"LB" : 10,
	"RB" : 2,
    },
}

# Mouse is polled at 62.5 Hz (obtained using evtest)
# Atari ST screen vertical freq in 50 Hz
REFRESH_PERIOD = 1 / 80
MAX_TICK_PERIOD = REFRESH_PERIOD / 2
MIN_TICK_PERIOD = 1 / 2000 # 2 KHz
TICK_PERIOD_DECAY = 1.01
STATS_PERIOD = 0.5 # seconds

A_SIGNAL = (0, 1, 1, 0)
B_SIGNAL = (0, 0, 1, 1)

def rpi_init(board_version):
    pins = BOARDS_CONFIG[board_version]
    return {k:LED(v) for k,v in pins.items()}

class StMouse:
    def __init__(self, board_version, xy_scale):
        self.x_state = 0
        self.y_state = 0
        self.x_delta = 0
        self.y_delta = 0
        self.xy_scale = xy_scale
        self.tick_period = MAX_TICK_PERIOD
        self.worst_delay = 0
        # Initialize and turn off every line
        self.signals = rpi_init(board_version)
        for sig in self.signals.values():
            sig.off()

    def x_step(self, dir):
        """dir can be 1 for right or -1 for left"""
        self.x_state = (self.x_state + dir) % 4
        if A_SIGNAL[self.x_state]: self.signals["XA"].on()
        else: self.signals["XA"].off()
        if B_SIGNAL[self.x_state]: self.signals["XB"].on()
        else: self.signals["XB"].off()

    def y_step(self, dir):
        self.y_state = (self.y_state + dir) % 4
        if A_SIGNAL[self.y_state]: self.signals["YB"].on()
        else: self.signals["YB"].off()
        if B_SIGNAL[self.y_state]: self.signals["YA"].on()
        else: self.signals["YA"].off()

    def btn_left(self, val):
        if val: self.signals["LB"].on()
        else  : self.signals["LB"].off()

    def btn_right(self, val):
        if val: self.signals["RB"].on()
        else  : self.signals["RB"].off()

    def x_move(self, val):
        self.x_delta += val

    def y_move(self, val):
        self.y_delta += val

    def update_tick_period(self):
        delta_steps = max(abs(self.x_delta), abs(self.y_delta)) / self.xy_scale
        if delta_steps >= 1:
            self.tick_period = min( self.tick_period, REFRESH_PERIOD / delta_steps ) # Only faster
            self.tick_period = max( self.tick_period, MIN_TICK_PERIOD )
            self.tick_period = min( self.tick_period, MAX_TICK_PERIOD )

    def update_worst_delay(self, ev_time):
        delta_steps = max(abs(self.x_delta), abs(self.y_delta)) / self.xy_scale
        if delta_steps >= 1: # We can't tell if we don't have any step in queue
            evt_delay = time.time() - ev_time
            sig_delay = evt_delay + delta_steps * self.tick_period
            self.worst_delay = max(self.worst_delay, sig_delay)

    def decay_tick_period(self):
        delta_steps = max(abs(self.x_delta), abs(self.y_delta)) / self.xy_scale
        if delta_steps < 1:
            self.tick_period = self.tick_period * TICK_PERIOD_DECAY
            self.tick_period = min(self.tick_period, MAX_TICK_PERIOD)

    def get_tick_period(self):
        return self.tick_period

    def signals_tick(self):
        # Move mouse pointer
        if abs(self.x_delta) >= self.xy_scale:
            # increment by (+/-) self.xy_scale
            inc = self.xy_scale * self.x_delta // abs(self.x_delta)
            self.x_delta -= inc # Works for positive and negative alike
            self.x_step(inc // self.xy_scale) # Step is by +/- 1
        if abs(self.y_delta) >= self.xy_scale:
            inc = self.xy_scale * self.y_delta // abs(self.y_delta)
            self.y_delta -= inc
            self.y_step(inc // self.xy_scale)
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

@click.command()
@click.option("--board", default="v2.1", help="Board revision.")
@click.option("--device", default="/dev/input/event0", help="Input device to use.")
@click.option("--xy-scale", default=2, help="Scale for XY mouse movements (more = slower mouse).")
def main(board, device, xy_scale):
    sm = StMouse(board_version=board, xy_scale=xy_scale)
    dev = idev.InputDevice(device=device, blocking=False)

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
