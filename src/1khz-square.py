#!/usr/bin/env python3
"""Used for testing purpose"""

import time
from gpiozero import LED

TICK_PERIOD = 1/1000 # 1 KHz period

def main():
    led = LED(18)
    
    next_tick = time.monotonic()
    while True:
        next_tick += TICK_PERIOD/2
        if led.is_active: led.off()
        else: led.on()
        try:
            time.sleep( next_tick - time.monotonic() )
        except ValueError:
            pass

main()
