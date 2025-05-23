import sys
import time
import os
import json
import numpy as np
import serial
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QGridLayout,
    QLineEdit, QFileDialog, QGroupBox, QButtonGroup, QRadioButton, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import flir_camera_tools.cam_tools as ct
import utils.cam_utils as cu
import PySpin

ARDUINO_PORT = "COM3"
USER_CONFIG_DIR = os.path.join(os.getcwd(), "users")
os.makedirs(USER_CONFIG_DIR, exist_ok=True)



class ArcardieGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.init_window()

        self.system = None
        self.cam = None
        self.dev = None
        self.image = None
        self.save_folder = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.modified = False

        self.init_camera()
        self.init_serial()

        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)

        self.init_ui()

    def init_window(self):
        self.setWindowTitle("Phenotype-o-mat GUI")
        self.setGeometry(100, 100, 400, 700)

    def init_camera(self):
        self.cam_status = False
        if not ct.detect_cams():
            sys.exit()
        self.system = ct.ps.System.GetInstance()
        cam_list = self.system.GetCameras()
        self.cam = cam_list[0]
        self.cam.Init()
        self.cam_status = True

    def init_serial(self):
        self.arduino_status = False
        try:
            self.dev = serial.Serial(ARDUINO_PORT, timeout=2)
            time.sleep(2)
            self.dev.write(b"SET LED_TRANS_STATUS 1;")
            self.arduino_status = True
        except:
            self.dev = None

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        layout = QVBoxLayout()
        main_layout.addLayout(layout)
        # Status
        self.status_label = QLabel("Camera: " + ("Connected" if self.cam_status else "Disconnected"))
        self.status_label.setStyleSheet(f"color: {'green' if self.cam_status else 'red'}; font-weight: bold;")
        self.arduino_label = QLabel("Arduino: " + ("Connected" if self.arduino_status else "Disconnected"))
        self.arduino_label.setStyleSheet(f"color: {'green' if self.arduino_status else 'red'}; font-weight: bold;")
        layout.addWidget(self.status_label)
        layout.addWidget(self.arduino_label)

        # Toggle preview
        self.preview_label = QLabel("Live Preview")
        self.preview_label.setFixedSize(640, 480)
        self.preview_label.setStyleSheet("border: 1px solid black;")
        main_layout.addWidget(self.preview_label)

        self.preview_btn = QPushButton("Start Preview")
        self.preview_btn.clicked.connect(self.toggle_preview)
        layout.addWidget(self.preview_btn)

        # User selection
        self.user_selector = QComboBox()
        self.user_selector.setEditable(True)
        layout.addWidget(QLabel("User:"))
        layout.addWidget(self.user_selector)
        self.load_users()
        self.user_selector.setCurrentIndex(-1)
        self.user_selector.currentTextChanged.connect(self.load_user_config)
        layout.addWidget(self.make_divider())

        # Mode selection
        mode_group = QGroupBox("Mode")
        self.mode_buttons = QButtonGroup(self)
        single_btn = QRadioButton("Single Image")
        timelapse_btn = QRadioButton("Timelapse")
        video_btn = QRadioButton("Video")
        single_btn.setChecked(True)
        self.mode_buttons.setExclusive(True)
        self.mode_buttons.addButton(single_btn, 0)
        self.mode_buttons.addButton(timelapse_btn, 1)
        self.mode_buttons.addButton(video_btn, 2)
        vbox = QVBoxLayout()
        vbox.addWidget(single_btn)
        vbox.addWidget(timelapse_btn)
        vbox.addWidget(video_btn)
        mode_group.setLayout(vbox)
        layout.addWidget(mode_group)
        self.mode_buttons.buttonClicked.connect(self.update_field_states)

        # Parameters
        #self.res_x = QLineEdit()
        #self.res_y = QLineEdit()
        self.expo_input = QLineEdit()
        self.framerate_input = QLineEdit()
        self.duration_input = QLineEdit()
        #self.res_x.setPlaceholderText("Width [8 - 1440]")
        #self.res_y.setPlaceholderText("Height [6 - 1080]")
        self.expo_input.setPlaceholderText("Exposure (μs)")
        self.framerate_input.setPlaceholderText("Interval (min between frames)")
        self.duration_input.setPlaceholderText("Duration (min, for video/timelapse)")
        # Track changes to mark as modified
        for field in [self.expo_input, self.framerate_input, self.duration_input]:
            field.textChanged.connect(self.mark_modified)

        layout.addWidget(self.make_divider())
        param_layout = QGridLayout()
        #param_layout.addWidget(QLabel("Width:"), 0, 0)
        #param_layout.addWidget(self.res_x, 0, 1)
        #param_layout.addWidget(QLabel("Height:"), 1, 0)
        #param_layout.addWidget(self.res_y, 1, 1)
        param_layout.addWidget(QLabel("Exposure (μs):"), 2, 0)
        param_layout.addWidget(self.expo_input, 2, 1)
        param_layout.addWidget(QLabel("Interval (min):"), 3, 0)
        param_layout.addWidget(self.framerate_input, 3, 1)
        param_layout.addWidget(QLabel("Duration (min):"), 4, 0)
        param_layout.addWidget(self.duration_input, 4, 1)
        layout.addWidget(QLabel("Resolution: 1440 x 1080 (fixed)"))
        layout.addLayout(param_layout)

        # Save parametersS
        self.save_btn = QPushButton("Save Parameters")
        self.save_btn.clicked.connect(self.save_user_config)
        self.save_status = QLabel("")
        layout.addWidget(self.save_btn)
        layout.addWidget(self.save_status)
        layout.addWidget(self.make_divider())

        # LED checkboxes
        color_group = QGroupBox("Color exposition")
        grid = QGridLayout()
        self.red_cb = QCheckBox("Red")
        self.blue_cb = QCheckBox("Blue")
        self.yellow_cb = QCheckBox("Yellow")
        self.green_cb = QCheckBox("Green")
        grid.addWidget(self.red_cb, 0, 0)
        grid.addWidget(self.blue_cb, 0, 1)
        grid.addWidget(self.yellow_cb, 1, 0)
        grid.addWidget(self.green_cb, 1, 1)
        color_group.setLayout(grid)
        layout.addWidget(color_group)

        # Browsing
        layout.addWidget(self.make_divider())
        self.browse_button = QPushButton('Browse Folder')
        self.browse_button.clicked.connect(self.browse_folder)
        layout.addWidget(self.browse_button)
        self.path_display = QLabel(f"Save Path: {self.save_folder}")
        layout.addWidget(self.path_display)

        layout.addWidget(self.make_divider())
        start_btn = QPushButton("Start")
        layout.addWidget(start_btn)
        start_btn.clicked.connect(self.start_acquisition)

        self.setLayout(layout)
        self.update_field_states()

    def toggle_preview(self):
        if self.preview_timer.isActive():
            self.preview_timer.stop()
            self.preview_btn.setText("Start Preview")
            print("Preview stopped.")
            if self.dev:
                self.dev.write(b"SET LED_TRANS_STATUS 1;")  
        else:
            self.preview_timer.start(100)  # every 100 ms
            self.preview_btn.setText("Stop Preview")
            print("Preview started.")
            if self.dev:
                self.dev.write(b"SET LED_TRANS_STATUS 0;")

    def update_preview(self):
        if self.cam:
            try:
                self.cam.BeginAcquisition()
                img = self.cam.GetNextImage()
                if img.IsIncomplete():
                    return
                np_img = img.GetNDArray()
                img.Release()
                self.cam.EndAcquisition()

                h, w = np_img.shape
                qimg = QImage(np_img.data, w, h, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(qimg)
                self.preview_label.setPixmap(
                    pixmap.scaled(
                        self.preview_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation  # <- adds better scaling quality
                    )
                )
            except PySpin.SpinnakerException as e:
                print("Preview error:", e)


    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.save_folder)
        if folder:
            self.save_folder = folder
            self.path_display.setText(f"Save Path: {self.save_folder}")
            self.mark_modified()

    def load_users(self):
        self.user_selector.clear()
        users = [f.replace(".json", "") for f in os.listdir(USER_CONFIG_DIR) if f.endswith(".json")]
        self.user_selector.addItems(sorted(users))

    def load_user_config(self, name):
        path = os.path.join(USER_CONFIG_DIR, f"{name}.json")
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                cfg = json.load(f)

                #self.res_x.setText(cfg.get("res_x", ""))
                #self.res_y.setText(cfg.get("res_y", ""))
                self.expo_input.setText(cfg.get("exposure", ""))
                self.framerate_input.setText(cfg.get("framerate", ""))
                self.duration_input.setText(cfg.get("duration", ""))

                # Mode
                mode_id = cfg.get("mode", 0)
                if self.mode_buttons.button(mode_id):
                    self.mode_buttons.button(mode_id).setChecked(True)
                    self.update_field_states()

                # LED colors
                colors = cfg.get("colors", {})
                self.red_cb.setChecked(colors.get("red", False))
                self.blue_cb.setChecked(colors.get("blue", False))
                self.yellow_cb.setChecked(colors.get("yellow", False))
                self.green_cb.setChecked(colors.get("green", False))

                # Output directory
                self.save_folder = cfg.get("save_folder", self.save_folder)
                self.path_display.setText(f"Save Path: {self.save_folder}")

                self.save_status.setText("✅ Saved!")
                self.save_status.setStyleSheet("color: green;")
                self.modified = False
        except Exception as e:
            print("Error loading config:", e)


    def save_user_config(self):
        name = self.user_selector.currentText().strip()
        if not name:
            return
        config = {
        #    "res_x": self.res_x.text(),
        #    "res_y": self.res_y.text(),
            "exposure": self.expo_input.text(),
            "framerate": self.framerate_input.text(),
            "duration": self.duration_input.text(),
            "mode": self.mode_buttons.checkedId(),
            "colors": {
                "red": self.red_cb.isChecked(),
                "blue": self.blue_cb.isChecked(),
                "yellow": self.yellow_cb.isChecked(),
                "green": self.green_cb.isChecked(),
            },
            "save_folder": self.save_folder
        }
        with open(os.path.join(USER_CONFIG_DIR, f"{name}.json"), "w") as f:
            json.dump(config, f, indent=2)

        self.modified = False
        self.load_users()

    def mark_modified(self):
        if not self.modified:
            self.modified = True
            self.save_status.setText("✏️ Modified - not saved")
            self.save_status.setStyleSheet("color: orange;")

    def update_field_states(self):
        mode = self.mode_buttons.checkedId()
        self.duration_input.setDisabled(mode == 0)       # Only enable for video and timelapse
        self.framerate_input.setDisabled(mode != 1)      # Only enable for timelapse

    def make_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def start_acquisition(self):
        if not self.cam:
            print("❌ No camera initialized.")
            return

        mode_id = self.mode_buttons.checkedId()
        mode_map = {0: "single", 1: "timelapse", 2: "video"}
        mode = mode_map.get(mode_id, "single")

        # --- Parse Resolution ---
        """
        try:
            width = int(self.res_x.text())
            height = int(self.res_y.text())
            if cu.set_resolution(self.cam, width, height):
                print(f"✅ Resolution set to {width}x{height}")
            else:
                print("❌ Failed to set resolution")
                return
        except ValueError:
            print("❌ Invalid resolution input")
            return
        """
        width = self.cam.Width.GetValue()
        height = self.cam.Height.GetValue()
        print(f"📷 Camera actual resolution: {width} x {height}")
        # --- Parse Exposure ---
        try:
            exposure = int(self.expo_input.text())
            if cu.set_exposure(self.cam, exposure):
                print(f"✅ Exposure set to {exposure} μs")
            else:
                print("❌ Failed to set exposure")
                return
        except ValueError:
            print("❌ Invalid exposure input")
            return

        # --- Parse Duration ---
        try:
            duration_min = float(self.duration_input.text())
        except ValueError:
            duration_min = 1.0  # default to 1 min
            print("⚠️ Invalid duration input, using 1 min")

        # --- Parse Interval (Timelapse mode only) ---
        if mode == "timelapse":
            try:
                interval_min = float(self.framerate_input.text())
                fps = 1 / (interval_min * 60)
                if fps >= 1.0:
                    if cu.set_framerate(self.cam, fps):
                        print(f"✅ Camera framerate set to {fps:.2f} Hz")
                    else:
                        print("⚠️ Failed to set framerate (might be out of bounds)")
                else:
                    print(f"ℹ️ Interval {interval_min} min too long (fps={fps:.4f} Hz); skipping set_framerate.")
            except ValueError:
                print("❌ Invalid interval input for timelapse")
                return

        # --- Barcode & Colors (optional for filenames) ---
        barcode = self.user_selector.currentText().strip() or "000000"
        prefix = mode

        # --- Run Mode-Specific Capture ---
        print(f"🚀 Starting mode: {mode}")
        if mode == "single":
            cu.run_single_image(self.cam, self.save_folder, prefix, barcode)

        elif mode == "timelapse":
            colors = {
                "670": self.red_cb.isChecked(),
                "460": self.blue_cb.isChecked(),
                "590": self.yellow_cb.isChecked(),
                "535": self.green_cb.isChecked()
            }
            cu.run_timelapse(self.cam, duration_min, interval_min, self.save_folder, prefix, barcode, self.dev, colors)
        elif mode == "video":
            cu.run_video(self.cam, duration_min * 60, self.save_folder, prefix, barcode, fps=30)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ArcardieGUI()
    gui.show()
    sys.exit(app.exec_())
