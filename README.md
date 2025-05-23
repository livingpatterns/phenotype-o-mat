# Phenotype-o-mat

A GUI-based tool for time-lapse and image acquisition using a FLIR/Spinnaker camera and an Arduino-controlled lighting system.

## Requirements

- Python 3.10+
- Camera: FLIR Blackfly or similar (compatible with PySpin SDK)
- Arduino with LED control firmware
- USB3 connection to camera
- Serial connection to Arduino

## How to Use

1. **Connect your devices**
   - Connect the **camera** via USB.
   - Connect the **Arduino** to a serial port (e.g. COM3 on Windows).

2. **Launch the GUI**
   
   Type the following line in the terminal: 
   ```bash
   python phenotypeomat_GUI.py

4. **Set up your session**

Select or enter your name in the dropdown at the top. If it's a new name, a new config file will be created in the users/ folder.
Configure your acquisition parameters:
  - Exposure time (in microseconds)
  - Interval between timelapse frames (in minutes)
  - Total duration of timelapse (in minutes)
  - LED colors to activate (Red = 670 nm, Blue = 460 nm, Green = 535 nm, Yellow = 590 nm)
  - Output directory for saving images
  - Acquisition mode: Single Image, Timelapse, or Video (Video not yet implemented)

5. **Use the live preview**

   Click `Start Preview` to see the live image from the camera.
   Use it to adjust the focus manually.
   The LED bed turns ON during preview and OFF when preview stops.

7. **Start acquisition**

    Click the `Start` button once everything is set.

    The software will turn OFF the colored LEDs and turn ON the LED bed only during image capture.
