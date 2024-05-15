#!/usr/bin/env python3
import time
from gpiozero import LED
import inputdevice as idev

BOARDS_CONFIG = {
    "v2.1": {
        "port0": {
            "down": 27,
            "up": 22,
            "left": 17,
            "right": 4,
            "fire": 10,
        },
        "port1": {
            "down": 6,
            "up": 13,
            "left": 5,
            "right": 0,
            "fire": 19,
        },
    },
}

def rpi_init(board_version, port_id):
    pins = BOARDS_CONFIG[board_version][port_id]
    return {k:LED(v) for k,v in pins.items()}

def main(device, board_version, port_id):
    port = rpi_init(board_version, port_id)
    while True:
        try:
            dev = idev.InputDevice(device)
            print(f"Opened device: {device}")
            while True:
                _, _, ev_type, ev_code, ev_value = dev.get_event()
                if  ev_type == idev.EV_ABS:
                    if   ev_code == idev.ABS_HAT0X:
                        print(f"HAT0X move: {ev_value}")
                        if   ev_value == -1: port["left"].on()
                        elif ev_value ==  1: port["right"].on()
                        else: # ev_value == 0 when releasing a button
                            port["left"].off()
                            port["right"].off()
                    elif ev_code == idev.ABS_HAT0Y:
                        print(f"HAT0Y move: {ev_value}")
                        if   ev_value == -1: port["up"].on()
                        elif ev_value ==  1: port["down"].on()
                        else: # ev_value == 0 when releasing a button
                            port["down"].off()
                            port["up"].off()
                elif ev_type == idev.EV_KEY and ev_code == idev.BTN_SOUTH:
                        print(f"FIRE button: {ev_value}")
                        if ev_value == 1: port["fire"].on()
                        else: port["fire"].off()
        except OSError as e:
            # Sometimes gamepads gets disconnected with crap cables
            print(f"Error getting event: {e}")
            time.sleep(0.2)

if __name__ == "__main__":
    main("/dev/input/event6", "v2.1", "port1")
