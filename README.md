# Phenotype-o-mat

A GUI-based tool for time-lapse and single image acquisition using a FLIR Blackfly (or compatible) camera and an Arduino-controlled LED system. Designed to support experiments with controllable lighting and repeatable imaging protocols.

## Requirements

- Python 3.10+
- FLIR Blackfly camera (compatible with Spinnaker / PySpin)
- Arduino (connected via serial, e.g. COM3 on Windows) with LED firmware
- USB3 connection to the camera
- PyQt5, NumPy, OpenCV, PySpin SDK

## How to Use

### 1. Connect your devices

- Connect the **camera** via USB.
- Connect the **Arduino** via USB (e.g. `COM3` on Windows).

### 2. Launch the GUI

```bash
python phenotypeomat_GUI.py
```
### 3. Set up your session

At the top of the GUI, select your user name or enter a new name. A configuration file will be saved in the users/ directory.

Configure the acquisition parameters:
- Exposure time (in microseconds)
- Interval between images (in minutes, for timelapse)
- Total duration (in minutes)
- LED colors to activate (Red = 670 nm, Blue = 460 nm, Green = 535 nm, Yellow = 590 nm)
- Output folder for saving images
- Mode: Single Image or Timelapse (Video is not yet implemented)

### 4. Use live preview (optional)

Click `Start Preview` to activate the camera and see a live image.
Use this to manually adjust the focus.
The LED bed turns ON during preview and is turned OFF when preview stops.

### 5. Start acquisition

Click `Start` to begin the capture process.
During image capture:
1. The LED bed turns ON
2. All color LEDs are temporarily turned OFF
3. Then restored between frames

Captured images are saved automatically in your selected directory.

## Source & Inspiration

This project is adapted and extended from the open protocol developed by Arcadia Science (https://github.com/Arcadia-Science/arcadia-phenotypeomat-protocol/tree/main)
