import cv2
import numpy as np
import time as tm
import os
import ctypes

# --- 🔧 DLL + SDK setup for gxipy ---
gx_root = r"C:\Program Files\Daheng Imaging\GalaxySDK"
dll_path = os.path.join(gx_root, "APIDll", "Win64")  # ← use Win64!

# Add to environment variables
os.environ["GALAXY_SDK_ROOT"] = gx_root
os.environ["GALAXY_GENICAM_ROOT"] = os.path.join(gx_root, "GenICam")
os.environ["PATH"] = dll_path + os.pathsep + os.environ["PATH"]

# ✅ Force preload GxIAPI.dll
gx_dll = os.path.join(dll_path, "GxIAPI.dll")
if not os.path.exists(gx_dll):
    raise FileNotFoundError(f"❌ Could not find GxIAPI.dll at: {gx_dll}")
ctypes.CDLL(gx_dll)

import gxipy as gx

def bcode_read():
    bcode = input("Scan barcode now or press enter for no barcode ")
    return bcode if bcode else "000000"


def detect_cams(n=1):
    device_manager = gx.DeviceManager()
    device_manager.update_device_list()
    return len(device_manager.get_all_device_info()) >= n


def init_cam():
    device_manager = gx.DeviceManager()
    device_manager.update_device_list()
    if len(device_manager.get_all_device_info()) == 0:
        raise RuntimeError("No Daheng cameras found.")
    cam = device_manager.open_device_by_index(1)
    cam.stream_on()
    return cam


def set_resolution(cam, width, height):
    cam.Width.set(width)
    cam.Height.set(height)


def set_binning(cam, x_binning, y_binning):
    cam.BinningHorizontal.set(x_binning)
    cam.BinningVertical.set(y_binning)


def set_gain_mode(cam, mode="once"):
    # Daheng doesn't use the same "once" logic as FLIR; usually either manual or auto
    cam.GainAuto.set("ON" if mode.lower() == "continuous" else "OFF")


def get_gain_mode(cam):
    return cam.GainAuto.get()


def set_expos_mode(cam, mode="once"):
    cam.ExposureAuto.set("ON" if mode.lower() == "continuous" else "OFF")


def get_expos_mode(cam):
    return cam.ExposureAuto.get()


def set_expos_time(cam, exposure_time_us):
    cam.ExposureAuto.set("OFF")
    cam.ExposureTime.set(exposure_time_us)


def set_acq_cont(cam):
    cam.AcquisitionMode.set("Continuous")


def grab_images(cam, length=None, n_frames=None):
    if length is None and n_frames is None:
        n_frames = 1
    elif length is not None and n_frames is None:
        # estimate framerate by trying one image
        frame_rate = 10  # assume 10fps default if unknown
        n_frames = int(length * frame_rate)
    elif length is not None and n_frames is not None:
        print("Specify only one of 'length' or 'n_frames'")
        return

    images = []
    timestamps = []

    for _ in range(n_frames):
        raw = cam.data_stream[0].get_image(timeout=1000)
        if raw is None:
            continue
        rgb_image = raw.convert("RGB")
        img_np = rgb_image.get_numpy_array()
        images.append(img_np)
        timestamps.append(tm.time())

    return images, timestamps


def save_avi(images, frame_rate=10.0, barcode="00000", prefix="video", path="./", is_color=True):
    if not os.path.exists(path):
        os.makedirs(path)

    tme = int(tm.time())
    height, width, _ = images[0].shape
    filename = os.path.join(path, f"{prefix}_{barcode}_{tme}.avi")
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(filename, fourcc, frame_rate, (width, height), is_color)

    for img in images:
        out.write(img)

    out.release()
    print(f"Saved video to {filename}")


def get_framerate(cam):
    try:
        return cam.AcquisitionFrameRate.get()
    except:
        return 10.0  # fallback default


def set_framerate(cam, frame_rate=10.0):
    cam.AcquisitionFrameRateEnable.set(True)
    cam.AcquisitionFrameRate.set(frame_rate)
