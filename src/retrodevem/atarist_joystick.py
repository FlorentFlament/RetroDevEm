import time
import logging
import click

from gpiozero import LED
from gpiozero.exc import BadPinFactory

from . import inputdevice as idev

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

def process_input_events(input_device, board_signals):
    dev = idev.InputDevice(input_device)
    logger.info(f"Opened device: {input_device}")
    while True:
        _, _, ev_type, ev_code, ev_value = dev.get_event()
        if  ev_type == idev.EV_ABS:
            if   ev_code == idev.ABS_HAT0X:
                logger.info(f"HAT0X move: {ev_value}")
                if   ev_value == -1: board_signals["left"].on()
                elif ev_value ==  1: board_signals["right"].on()
                else: # ev_value == 0 when releasing a button
                    board_signals["left"].off()
                    board_signals["right"].off()
            elif ev_code == idev.ABS_HAT0Y:
                logger.info(f"HAT0Y move: {ev_value}")
                if   ev_value == -1: board_signals["up"].on()
                elif ev_value ==  1: board_signals["down"].on()
                else: # ev_value == 0 when releasing a button
                    board_signals["down"].off()
                    board_signals["up"].off()
        elif ev_type == idev.EV_KEY and ev_code == idev.BTN_SOUTH:
                logger.info(f"FIRE button: {ev_value}")
                if ev_value == 1: board_signals["fire"].on()
                else: board_signals["fire"].off()

@click.command()
@click.option("--board",  "-b", default="v2.1", type=click.Choice(['v2.0', 'v2.1']), help="Board revision.", show_default=True)
@click.option("--device", "-d", default="/dev/input/event0", help="Input device to use.", show_default=True)
@click.option("--port",   "-p", default=1, type=click.Choice(['0', '1']), help="Board/Atari ST port to connect the joystick to.", show_default=True)
@click.option("--debug/--no-debug", help="Display debugging information.", show_default=True)
def main(device, board, port, debug):
    """Send joystick/gamepad events to an Atari ST connected to the
    RetroDevEm board.  Usage example: atarist-joystick --board v2.0
    --device /dev/input/event0 --port 0

    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    try:
        signals = rpi_init(board, port)
        while True:
            try:
                process_input_events(device, signals)
            except OSError as e:
                # Sometimes gamepads get temporarily disconnected with crap cables
                logger.warning(f"Error getting event: {e}")
            time.sleep(0.2)
    except BadPinFactory as e:
        logger.error(f"Failed to initialize GPIO pins: {e}")
        logger.error( "This program expects to be running on a Raspberry Pi. Is that the case ?")

if __name__ == "__main__":
    main()
