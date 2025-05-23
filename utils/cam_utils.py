import time as tm
from datetime import datetime
import os
import cv2
import PySpin as ps

def get_resolution_range(cam):
    try:
        width_min = cam.Width.GetMin()
        width_max = cam.Width.GetMax()
        height_min = cam.Height.GetMin()
        height_max = cam.Height.GetMax()
        return (width_min, width_max), (height_min, height_max)
    except ps.SpinnakerException as ex:
        print(f"Error retrieving resolution range: {ex}")
        return None


def set_resolution(cam, width, height):
    try:
        if width > cam.Width.GetMax() or width < cam.Width.GetMin():
            raise ValueError("Width out of range.")
        if height > cam.Height.GetMax() or height < cam.Height.GetMin():
            raise ValueError("Height out of range.")
        cam.Width.SetValue(width)
        cam.Height.SetValue(height)
        return True
    except (ps.SpinnakerException, ValueError) as ex:
        print(f"Error setting resolution: {ex}")
        return False


def set_exposure(cam, exposure_us):
    try:
        cam.ExposureAuto.SetValue(ps.ExposureAuto_Off)
        cam.ExposureTime.SetValue(min(exposure_us, cam.ExposureTime.GetMax()))
        return True
    except ps.SpinnakerException as ex:
        print(f"Error setting exposure: {ex}")
        return False


def set_framerate(cam, fps):
    try:
        cam.AcquisitionFrameRateEnable.SetValue(True)
        cam.AcquisitionFrameRate.SetValue(fps)
        return True
    except ps.SpinnakerException as ex:
        print(f"Error setting framerate: {ex}")
        return False




def save_avi(images, frame_rate=30.0, barcode="000000", prefix="capture", path="./", is_color=False):
    """Saves a list of images as an AVI using OpenCV."""
    if not images:
        print("No images to save.")
        return

    tme = int(tm.time())
    height, width = images[0].shape
    fourcc = 0  # uncompressed (can be cv2.VideoWriter_fourcc(*'XVID') for .avi with compression)
    filename = f"{prefix}_{barcode}_{tme}.avi"
    filepath = path if path.endswith("/") else path + "/"
    filepath += filename

    writer = cv2.VideoWriter(filepath, fourcc, frame_rate, (width, height), is_color)
    for img in images:
        if is_color:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        writer.write(img)
    writer.release()

    print(f"💾 Video saved: {filepath}")



def run_single_image(cam, output_dir, prefix="single", barcode="000000"):
    """Capture and save a single image."""
    cam.BeginAcquisition()
    img = cam.GetNextImage(1000)
    if img.IsIncomplete():
        print("⚠️ Image incomplete. Skipping.")
        cam.EndAcquisition()
        return
    np_img = img.GetNDArray()
    img.Release()
    cam.EndAcquisition()

    timestamp = int(tm.time())
    filename = f"{prefix}_{barcode}_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    cv2.imwrite(filepath, np_img)
    print(f"✅ Single image saved: {filepath}")


def grab_image(cam):
    try:
        cam.BeginAcquisition()
        timeout = 1000
        timestamp = tm.time()
        image = cam.GetNextImage(timeout)
        image.Release()
        cam.EndAcquisition()
        return image, timestamp
    except ps.SpinnakerException as ex:
        cam.EndAcquisition()
        print("Error: %s" % ex)
        return False

def run_timelapse(cam, duration_min, interval_min, path, prefix, barcode, dev, colors):

    total_frames = int(duration_min / interval_min)
    print(f"⏱️ Capturing {total_frames} frames, every {interval_min} minutes")

    set_color_leds(dev, colors, on=False)
    set_led_bed(dev, on=False)

    for i in range(total_frames):
        print(f"📸 Capturing frame {i+1}/{total_frames}")

        # Switch lights
        set_color_leds(dev, colors, on=False)
        set_led_bed(dev, on=True)
        tm.sleep(5)  # small delay for lighting to stabilize

        # Capture
        cam.BeginAcquisition()
        img = cam.GetNextImage()
        np_img = img.GetNDArray()
        img.Release()
        cam.EndAcquisition()

        # Save
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(path, f"{prefix}_{barcode}_{ts}.png")
        cv2.imwrite(filename, np_img)
        print(f"💾 Saved: {filename}")

        # Restore lights
        #set_led_bed(dev, on=False)
        set_color_leds(dev, colors, on=True)

        if i < total_frames - 1:
            tm.sleep(interval_min * 60)  # wait until next frame

    set_led_bed(dev, on=False)
    set_color_leds(dev, colors, on=False)

def set_led_bed(dev, on: bool):
    try:
        state = 0 if on else 1
        dev.write(b"SET LED_TRANS_STATUS " + bytes(f"{state};", "utf-8"))
    except Exception as e:
        print("Error setting LED bed:", e)

# Helper to control multiple color LEDs
def set_color_leds(dev, colors: dict, on: bool):
    try:
        state = 0 if on else 1
        for color, enabled in colors.items():
            if enabled:
                dev.write(bytes(f"SET LED_{color}_STATUS {state};", "utf-8"))
    except Exception as e:
        print("Error setting color LEDs:", e)

def run_video(cam, duration_sec, output_dir, prefix="video", barcode="000000", fps=30.0):
    """Capture a continuous stream and save it as a .avi video."""
    print(f"🎥 Starting video recording for {duration_sec} seconds")

    cam.BeginAcquisition()

    images = []
    timestamps = []

    start_time = tm.time()
    while tm.time() - start_time < duration_sec:
        img = cam.GetNextImage(1000)
        if img.IsIncomplete():
            print("⚠️ Skipped incomplete frame.")
            continue
        np_img = img.GetNDArray()
        images.append(np_img)
        timestamps.append(tm.time())
        img.Release()

    cam.EndAcquisition()

    if not images:
        print("❌ No frames captured.")
        return

    h, w = images[0].shape
    filename = f"{prefix}_{barcode}_{int(tm.time())}.avi"
    filepath = os.path.join(output_dir, filename)

    writer = cv2.VideoWriter(filepath, 0, fps, (w, h), False)
    for frame in images:
        writer.write(frame)
    writer.release()
    print(f"💾 Video saved: {filepath}")