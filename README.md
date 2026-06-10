# CUTTLE-DROID
C.U.T.T.L.E.-D.R.O.I.D.: Cuttlefish-Inspired Underwater Technology for Terrain Locomotion &amp; Exploration – Drone Robot for Ocean Inspection &amp; Discovery (Cuttle-Droid)

This repository contains the control code, setup code, 3D STL files and further supplementary used for the development of the **Cuttle-Droid** - a modular cuttlefish bio-inspired soft robot that mimics undulating wave-like motion for locomotion.

## Repository Structure

```
Cuttle-Droid/
│
├── design-files/                   # Mechanical design files
│   ├── mold /                      # STL files for casting fin and PFD files for assembly
│   └── robot/                      # STL and PDF files for assembly
│
└── robot-control-code/              # Arduino code for the main robot controller and pyhon code for remote control
    ├── RobotControlCode.ino         # Main controller logic For the robot
    ├── RobotRemoteController.py     # Remote controller script for manual steering
    └── Force_Test.py                # Python code for remotely controlling the force tests.
```

## Hardwatre Requirements
 - ESP32C3
 - Motor drivers and actuators
 - loadcell force sensor
 - hotspot or wifi access

## Software Requirements
- [Arduino IDE](https://www.arduino.cc/en/software)
- Python


## Design Files

## Code files
