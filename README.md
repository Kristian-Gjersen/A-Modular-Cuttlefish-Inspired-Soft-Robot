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

## Code files
