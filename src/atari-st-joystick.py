#!/usr/bin/env python3
import time
import logging
import click
from gpiozero import LED
import inputdevice as idev

logger = logging.getLogger(__name__)

BOARDS_CONFIG = {
    "v2.0": {
        0: { # Port 0 (i.e connector J2)
            "down" : 4,
            "up"   : 17,
            "left" : 3,
            "right": 22,
            "fire" : 27,
        },
        1: {
            "down" : 0,
            "up"   : 5,
            "left" : 11,
            "right": 13,
            "fire" : 6,
        },
    },
    "v2.1": {
        0: { # Port 1 (i.e connector J3)
            "down" : 27,
            "up"   : 22,
            "left" : 17,
            "right": 4,
            "fire" : 10,
        },
        1: {
            "down" : 6,
            "up"   : 13,
            "left" : 5,
            "right": 0,
            "fire" : 19,
        },
    },
}

def rpi_init(board_version, port_id):
    pins = BOARDS_CONFIG[board_version][port_id]
    return {k:LED(v) for k,v in pins.items()}

@click.command()
@click.option("--board", default="v2.1", help="Board revision.")
@click.option("--device", default="/dev/input/event0", help="Input device to use.")
@click.option("--port",  default=1, help="Board/Atari ST port to connect the joystick to.")
@click.option("--debug/--no-debug", help="Display debugging information.")
def main(device, board, port, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    signals = rpi_init(board, port)
    while True:
        try:
            dev = idev.InputDevice(device)
            logger.info(f"Opened device: {device}")
            while True:
                _, _, ev_type, ev_code, ev_value = dev.get_event()
                if  ev_type == idev.EV_ABS:
                    if   ev_code == idev.ABS_HAT0X:
                        logger.info(f"HAT0X move: {ev_value}")
                        if   ev_value == -1: signals["left"].on()
                        elif ev_value ==  1: signals["right"].on()
                        else: # ev_value == 0 when releasing a button
                            signals["left"].off()
                            signals["right"].off()
                    elif ev_code == idev.ABS_HAT0Y:
                        logger.info(f"HAT0Y move: {ev_value}")
                        if   ev_value == -1: signals["up"].on()
                        elif ev_value ==  1: signals["down"].on()
                        else: # ev_value == 0 when releasing a button
                            signals["down"].off()
                            signals["up"].off()
                elif ev_type == idev.EV_KEY and ev_code == idev.BTN_SOUTH:
                        logger.info(f"FIRE button: {ev_value}")
                        if ev_value == 1: signals["fire"].on()
                        else: signals["fire"].off()
        except OSError as e:
            # Sometimes gamepads gets disconnected with crap cables
            logger.warning(f"Error getting event: {e}")
            time.sleep(0.2)

if __name__ == "__main__":
    main()
