import os
import time
import json
import numpy as np
import cv2
import logging

import cameracapture as cc
import fileorga as fo
import ui_display as uid


class TimeLapse:
    """A class for creating time-lapse videos using a connected camera."""
    ON_RASPI = False # set True if this codes runs on a raspberr pi
    LOG_PATH = "log.txt"  # Path to the log file
    CAPTURE_INTERVAL = 5  # Interval between image captures in seconds

    def __init__(self):
        """Initializes the TimeLapseCamera object."""
        # Camera and image tracking
        self.state = {}
        self.state['active_project'] = ""
        self.state['selected_project'] = ""
        self.state['selected_project_index'] = 0
        self.state['img_capture_index'] = 0
        self.state['img_max_index'] = 0
        self.state['program_start_time'] = time.time()
        self.state['base_file_name'] = ''
        self.state['img_shown_index'] = 1
        self.state['playback_speed'] = 1
        self.state['playback_speed_index'] = 0
        self.state['default'] = False
        self.state['last_keypress'] = None


        self.img_file_prefix = "image_"
        
        self.key = None
        
        with open('config.json') as config_file:
            self.config = json.load(config_file)

        # SubModules
        self.camcap = cc.CameraCapture(self.config)
        self.fileorga = fo.FileOrga(self.config["projects_folder"])
        self.ui_display = uid.UIDisplay(self.config, self.state)

        # Timing and Playback controls

        self.last_picture_time = self.state['program_start_time'] - self.config["capture_interval"]
        self.state['last_keypress']  = time.time()

        self.read_log_file()        
        self.fileorga.setup_project(self.state)
        self.write_log_file()


    def read_log_file(self):
        """Reads the log file to resume the last session's state."""
        try:
            with open(self.LOG_PATH, "r") as log_file:
                self.state['active_project'] = log_file.readline().strip()
                self.state['img_capture_index'] = int(log_file.readline().strip())
                self.state['program_start_time'] = float(log_file.readline().strip())
        except FileNotFoundError:
            print("Log file not found. Starting with default values.")

    def write_log_file(self):
        """Writes the current state to the log file."""
        with open(self.LOG_PATH, "w") as log_file:
            log_file.write(f"{self.state['active_project']}\n{self.state['img_capture_index']}\n{self.state['program_start_time']}")

    def handle_key_press(self):
        """Handles key press events for playback control."""
        if self.key in [ord('d'), ord('a')]:
            self.state['last_keypress']  = time.time()
            self.state['default'] = False
            self.playback_speed = self.PLAYBACK_SPEEDS[self.playback_speed_index] * (-1 if self.key == ord('a') else 1)
            self.playback_speed_index = (self.playback_speed_index + 1) % len(self.PLAYBACK_SPEEDS)
            direction = "backward" if self.key == ord('a') else "forward"
            print(f"{direction} speed {self.playback_speed}")
        elif self.key == ord('s'):
            self.state['last_keypress']  = time.time()
            self.state['default'] = False
            if self.playback_speed > 0:
                self.playback_speed = self.DEFAULT_PLAYBACK_SPEED
            else:
                self.playback_speed = -1* self.DEFAULT_PLAYBACK_SPEED
            print("Play/Pause")
        elif self.key in [ord('e'), ord('w')]:
            self.state['last_keypress']  = time.time()
            self.state['default'] = False
            if self.key == ord('e'):
                self.selected_project_index = (self.selected_project_index + 1) % len(self.projects)
            else:
                self.selected_project_index = (self.selected_project_index - 1) % len(self.projects)
            self.selected_project = self.projects[self.selected_project_index]
            self.img_shown_index = 1
            print("Select", self.selected_project_index, self.selected_project)
            self.img_max_index = self.projects_dict[self.selected_project]
        elif self.key == 27: # escape key
            print("Quit")
            return False
        return True

    def main_loop(self):
        """Main loop for capturing images and handling playback."""
        while True:
            if not self.handle_key_press():
                break
            if time.time() - self.last_picture_time >= self.CAPTURE_INTERVAL:
                elapsed_time = int(time.time() - self.state['program_start_time'])
                base_img_path = os.path.join(self.config["projects_folder"], self.state["active_project"], self.img_file_prefix)
                img_path = base_img_path + str(self.state["img_capture_index"]) + ".jpg"
                self.camcap.image(elapsed_time, img_path)
                self.last_picture_time = time.time()
                if self.state["selected_project"] == self.state["active_project"]:
                    self.state["img_max_index"] = self.state["img_capture_index"]
                self.state["img_capture_index"] += 1
                self.write_log_file()

            self.ui_display.play_movie()
            if not self.state['default']:
                self.ui_display.return_to_default()

    def cleanup(self):
        """Releases resources and cleans up before exiting."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    timelapse = TimeLapse()
    timelapse.main_loop()
    timelapse.cleanup()