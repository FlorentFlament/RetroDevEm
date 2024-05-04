#!/usr/bin/env python3
from gpiozero import LED
import inputdevice as idev

# Update according to board design
JOY0_DOWN  = LED(27)
JOY0_UP    = LED(17)
JOY0_LEFT  = LED(4)
JOY0_RIGHT = LED(22)
JOY0_FIRE  = LED(10)

def dump_status():
    for sig in (JOY0_DOWN, JOY0_UP, JOY0_LEFT, JOY0_RIGHT, JOY0_FIRE):
        print(sig)

def main():
    dev = idev.InputDevice("/dev/input/event5")
    while True:
        _, _, ev_type, ev_code, ev_value = dev.get_event()
        if  ev_type == idev.EV_ABS:
            if   ev_code == idev.ABS_HAT0X:
                print(f"HAT0X move: {ev_value}")
                if   ev_value == -1: JOY0_LEFT.on()
                elif ev_value ==  1: JOY0_RIGHT.on()
                else: # ev_value == 0 when releasing a button
                    JOY0_LEFT.off()
                    JOY0_RIGHT.off()
            elif ev_code == idev.ABS_HAT0Y:
                print(f"HAT0Y move: {ev_value}")
                if   ev_value == -1: JOY0_UP.on()
                elif ev_value ==  1: JOY0_DOWN.on()
                else: # ev_value == 0 when releasing a button
                    JOY0_DOWN.off()
                    JOY0_UP.off()
        elif ev_type == idev.EV_KEY and ev_code == idev.BTN_SOUTH:
                print(f"FIRE button: {ev_value}")
                if ev_value == 1: JOY0_FIRE.on()
                else: JOY0_FIRE.off()

if __name__ == "__main__":
    main()
