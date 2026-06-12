# CUTTLE-DROID
C.U.T.T.L.E.-D.R.O.I.D.: Cuttlefish-Inspired Underwater Technology for Terrain Locomotion &amp; Exploration – Drone Robot for Ocean Inspection &amp; Discovery (Cuttle-Droid)

This repository contains the control code, setup code, 3D STL files and further supplementary used for the development of the **Cuttle-Droid** - a modular cuttlefish bio-inspired soft robot that mimics undulating wave-like motion for locomotion.

## Repository Structure

```
A-Modular-Cuttlefish-Inspired-Soft-Robot/
│
├── Design-Files/                    # Mechanical design files
│   ├── Mold/                        # STL files for casting fin
│   └── Robot/                       # STL files for the robot
│       └──Assembly-Guide/           # PDF guide on robot assembly
│
└── Robot-Control-Code/              # Arduino code for the main robot controller and pyhon code for remote control
    ├── RobotControlCode.ino         # Main controller logic For the robot
    ├── RobotRemoteController.py     # Remote controller script for manual steering
    └── Force_Test.py                # Python code for remotely controlling the force tests.
```

## Hardware Requirements
 - ESP32C3 microcontroller
 - Motor drivers and actuators
 - loadcell force sensor
 - hotspot or wifi access

## Software Requirements
- [Arduino IDE](https://www.arduino.cc/en/software)
- Python 3.11+ with packages:
    - `matplotlib`, `serial`, `keyboard`, `csv`, `time`, `socket`, `numpy`, `os`, `nidaqmx`

## Design Files

### Robot Parts
- All STL files for robot assembly located in `Design-Files/Robot`
- Guide for robot assembly and part count located in `Design-Files/Robot/Assembly-Guide`

### Mold
- STL files for Mold for fin casting found in `Design-Files/Mold`

## Code files
- `RobotControlCode.ino` contains the code that runs the robot. This code automatically start connecting to the provided hotspot and awaits requests for actuator inputs.
- `RobotRemoteController.py` contains the controller code for the laptop. This code will start searching for ESP32 on the hotspot and once connected it will allow for sending inputs to control the actuators on the robot. The controls works as follows:
```
W = speed up forward
S = slow down
A/D = soft turn left and right
Q/E = servo steering left and right
Z/C = differential turn left and right
SPACE = stop
```
- `Force_Test.py` contains the script used for doing force test readings on the robot. It sets up the ESP32, Daq, and Arduino to automatically perform the test that is selected. It will handle timing and duty cycle inputs to the robot.
