# RetroDevEm

<img src="pictures/retrodevem-v2.0-in-action-lowres.jpg" alt="RetroDevEm in action"/>

RetroDevEm (Retro Device Emulator) is a free (as in Free Software)
input devices (mouse and joystick) emulator for retro consoles and
computers (Atari 2600, Atari ST, Amstrad CPC, ...).  It allows using
any input device, recognized by Linux on the Raspberry Pi, on
unmodifed retro machines.  Programs collect events from input devices
and send the corresponding signals to the console or computer.

The project consists of 2 components:
- Hardware: A daughter printed circuit board, to be plugged on a Raspberry Pi;
- Software: Programs running on the Raspberry Pi.

The daughter board can be connected to the retro machines via DB-9
flat cables.

## Project focus

This project focuses on:
- Using off the shelf hardware ;
- Devices accuracy and low latency ;
- Simplicity ;
- Low CPU usage.

## Rationale

I bought a 30 Euros Atari ST mouse adapter from a hobbyist.  It only
works with ps/2 mice and the accuracy is okish.  Especially with slow
movements, the Atari ST pointer accuracy is bad.  So why not do
something better and make it free software ?

## Project details

### Hardware

<img src="pictures/rde-board-v2.1.jpg" alt="RetroDevEm Board v2.1"/>

A PCB (Printed Circuit Board), with:
- 2x ULN2003AN ICs (7 Darlington transistors per IC)
- 14x 15 KOhms resistors (optional)
- 1x 40 pins socket (Raspberry Pi connector)
- 2x 10 pins headers (Atari ports connectors)

#### About the resistors

Without resistors, the design works perfectly well.  The current drawn
on the Raspberry PI GPIO pins is 706 uA, for a 440 uA current flowing
out of the Atari ST mouse/joystick port.

With 15 KOhms resistors, the design works perfectly as well.  The
current on the Raspberry Pi GPIO pins in 113 uA, for a 440 uA current
on the Atari ST port side.

#### Board wiring

| RPI sig. | J1 pin | J2/J3 pins | Atari ST signals      | Amstrad CPC sig. | Atari 2600 sig. |
|----------|--------|------------|-----------------------|------------------|-----------------|
| GPIO2    | 3      | J2 9       | P0 Right Button       | COM2 (GND Joy 2) | Pot 1 (analog)  |
| GPIO3    | 5      | J2 5       | P0 Port 0 enable      | Fire 3 (undoc)   | Pot 0 (analog)  |
| GPIO4    | 7      | J2 4       | P0 YB / Right         | Right            | Right           |
| GPIO17   | 11     | J2 3       | P0 YA / Left          | Left             | Left            |
| GPIO27   | 13     | J2 2       | P0 XA / Down          | Down             | Down            |
| GPIO22   | 15     | J2 1       | P0 XB / Up            | Up               | Up              |
| GPIO10   | 19     | J2 6       | P0 Left Button / Fire | Fire 2 (default) | Fire            |
| GPIO9    | 21     | J3 9       | P1 Right Button       |                  |                 |
| GPIO11   | 23     | J3 5       | P1 Port 0 enable      |                  |                 |
| GPIO0    | 27     | J3 4       | P1 YB / Right         |                  |                 |
| GPIO5    | 29     | J3 3       | P1 YA / Left          |                  |                 |
| GPIO6    | 31     | J3 2       | P1 XA / Down          |                  |                 |
| GPIO13   | 33     | J3 1       | P1 XB / Up            |                  |                 |
| GPIO19   | 35     | J3 6       | P1 Left Button / Fire |                  |                 |

#### Generating the gerber files

In Kicad PCB editor:
- Run the DRC (Design Rule Checker)
- File -> Fabrication outputs -> Gerbers
- Select the output directory
- Include every layer except Margin, F.Courtyard and B.Courtyard
- Keep only the following "General Options" checked:
  - Plot the reference designators
  - Check zone fills before plotting
- Keep the default "Gerber Options"
- Click "Plot" button
- Then click on "Generate Drill Files..."
- In the "Drill File Format" section, select "Gerber X2"
- Then click "Generate Drill File"
- Create a zip archive from the gerber folder.

The generated archive can be checked in Kicad's Gerber viewer.

### Software

The RetroDevEm programs need to be installed on a Raspberry Pi
connected to the Atari ST through the RetroDevEm board (an RPI
daughter board).  The programs process events from input devices
(mouse, gamepad) and send corresponding signals to the retro machine
connected to the board.

#### Installation

You need to create a virtualenv on your Raspberry Pi and activate it:

```
$ virtualenv venv/retrodevem
created virtual environment CPython3.11.2.final.0-64 in 353ms
  creator CPython3Posix(dest=/home/florent/venv/retrodevem, clear=False, no_vcs_ignore=False, global=False)
  seeder FromAppData(download=False, pip=bundle, setuptools=bundle, wheel=bundle, via=copy, app_data_dir=/home/florent/.local/share/virtualenv)
    added seed packages: pip==23.0.1, setuptools==66.1.1, wheel==0.38.4
  activators BashActivator,CShellActivator,FishActivator,NushellActivator,PowerShellActivator,PythonActivator
$ source venv/retrodevem/bin/activate
```

Then RetroDevEm can be install with pip:

```
$ pip install retrodevem
Looking in indexes: https://pypi.org/simple, https://www.piwheels.org/simple
Collecting retrodevem
  Using cached retrodevem-0.2-py3-none-any.whl (22 kB)
Collecting click
  Using cached https://www.piwheels.org/simple/click/click-8.1.7-py3-none-any.whl (97 kB)
Collecting gpiozero
  Using cached https://www.piwheels.org/simple/gpiozero/gpiozero-2.0.1-py3-none-any.whl (150 kB)
Collecting lgpio
  Using cached lgpio-0.2.2.0-cp311-cp311-manylinux_2_34_aarch64.whl (364 kB)
Collecting colorzero
  Using cached https://www.piwheels.org/simple/colorzero/colorzero-2.0-py2.py3-none-any.whl (26 kB)
Requirement already satisfied: setuptools in ./venv/retrodevem/lib/python3.11/site-packages (from colorzero->gpiozero->retrodevem) (66.1.1)
Installing collected packages: lgpio, colorzero, click, gpiozero, retrodevem
Successfully installed click-8.1.7 colorzero-2.0 gpiozero-2.0.1 lgpio-0.2.2.0 retrodevem-0.2
```

#### Usage

Identify the input device files using `evtest`:

```
$ evtest
No device specified, trying to scan all of /dev/input/event*
Not running as root, no devices may be available.
Available devices:
/dev/input/event0:      vc4-hdmi-0
/dev/input/event1:      vc4-hdmi-0 HDMI Jack
/dev/input/event2:      vc4-hdmi-1
/dev/input/event3:      vc4-hdmi-1 HDMI Jack
/dev/input/event4:      Sony Interactive Entertainment Wireless Controller
/dev/input/event5:      Sony Interactive Entertainment Wireless Controller Motion Sensors
/dev/input/event6:      Sony Interactive Entertainment Wireless Controller Touchpad
/dev/input/event7:      Logitech USB Optical Mouse
Select the device event number [0-7]: ^C
```

Run the `atarist-mouse` program to emulate a mouse on the Atari ST:

```
$ atarist-mouse --device /dev/input/event7 &
[1] 1947
```

Run the `atarist-joystick` program to emulate a joystick on the Atari ST:

```
$ atarist-joystick --device /dev/input/event4 &
[2] 1951
```

Available options for the `atarist-mouse` program:

```
$ atarist-mouse --help
Usage: atarist-mouse [OPTIONS]

  Send mouse events to an Atari ST connected to the RetroDevEm board.  Usage
  example: atarist-mouse --board v2.0 --device /dev/input/event0 --port 0
  --speed 4

Options:
  --board TEXT          Board revision.  [default: v2.0]
  --device TEXT         Input device to use.  [default: /dev/input/event0]
  --port INTEGER        Board/Atari port to connect the mouse to.  [default:
                        0]
  --speed INTEGER       Mouse speed divider (more = slower).  [default: 2]
  --debug / --no-debug  Display debugging information.  [default: no-debug]
  --help                Show this message and exit.
```

Available options for the `atarist-joystick` program:

```
$ atarist-joystick --help
Usage: atarist-joystick [OPTIONS]

  Send joystick/gamepad events to an Atari ST connected to the RetroDevEm
  board.  Usage example: atarist-joystick --board v2.0 --device
  /dev/input/event0 --port 0

Options:
  --board TEXT          Board revision.  [default: v2.0]
  --device TEXT         Input device to use.  [default: /dev/input/event0]
  --port INTEGER        Board/Atari ST port to connect the joystick to.
                        [default: 1]
  --debug / --no-debug  Display debugging information.  [default: no-debug]
  --help                Show this message and exit.
```

### Additional information

- [Sourcing](sourcing.md)
- [Mechanical details](mechanical.md)

#### Consoles and computers DB9 wiring

##### Atari ST

| DB9 pins | Mouse P0            | Joystick P0            | Joystick P1 |
|----------|---------------------|------------------------|-------------|
| 1        | XB                  | Up                     | Up          |
| 2        | XA                  | Down                   | Down        |
| 3        | YA                  | Left                   | Left        |
| 4        | YB                  | Right                  | Right       |
| 5        |                     |                        | P0 enable   |
| 6        | Left But            | Fire                   | Fire        |
| 7        | +5V                 | +5V                    | +5V         |
| 8        | GND                 | GND                    | GND         |
| 9        | Right But           |                        |             |

##### Amstrad CPC & Atari 2600 Joystick

| DB9 pins | Amstrad CPC      | Atari 2600     |
|----------|------------------|----------------|
| 1        | Up               | Up             |
| 2        | Down             | Down           |
| 3        | Left             | Left           |
| 4        | Right            | Right          |
| 5        | Fire 3 (undoc)   | Pot 0 (analog) |
| 6        | Fire 2 (default) | Fire           |
| 7        | Fire 1 (extra)   | +5V            |
| 8        | COM1 (joy1)      | GND            |
| 9        | COM2 (joy2)      | Pot 1 (analog  |

Sources:
- [cpcwiki](https://www.cpcwiki.eu/index.php/Connector:Digital_joystick)
- [Atari ST Internals - page 73](https://archive.org/details/Atari_ST-Internals/page/72/mode/2up)

The first version will focus on the following use cases:
- Atari 2600: 1 joystick
- Atari ST: 1 mouse + 1 joystick
- Atari ST: 2 joysticks
- Amstrad CPC: 1 joystick

#### Schematics

<img src="pictures/retrodevem-v2.1-schematic.png" alt="RetroDevEm v2.1 schematic"/>

## Current status

### Atari ST

- Mouse emulation is working.  Latency is below 20 ms (i.e 1 frame at
  50 Hz) and CPU usage is below 10% of a core, for normal usage.
- Joystick emulation is working.  No latency, CPU usage below 1% of a
  core.

## Todo

- Configure RPI GPIO pins to pull-down input by default;
- Write blog article about the project.
- Implement auto-fire;
- Use [python-evdev][5] instead of custom `inputdevice` module.

## Links

- [Incremental encoder on Wikipedia][4]: describes the mouse signal
  expected by the Atari ST ;
- [ATARIPiMouse Github][1]: inspiration for writing the emulator in Python ;
- [Yaumataca][2]: inspiration for the "quadrature encoder" ;
- [Atari-Quadrature-USB-Mouse-Adapter][3]

[1]:https://github.com/backofficeshow/ATARIPiMouse
[2]:https://github.com/Slamy/Yaumataca
[3]:https://github.com/jjmz/Atari-Quadrature-USB-Mouse-Adapter
[4]:https://en.wikipedia.org/wiki/Incremental_encoder
[5]:https://python-evdev.readthedocs.io/en/latest/usage.html
