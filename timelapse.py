import time
import json
import os

from modules.program_state import ProgramState
from modules.camera_capture import CameraCapture
from modules.project_manager import ProjectManager
from modules.ui_display import UIDisplay


class TimeLapse:
    """A class for creating time-lapse videos using a connected camera."""
    LOG_PATH = "log.txt"  # Path to the log file

    def __init__(self):
        """Initializes the TimeLapse object."""
        # Load Configuration
        with open("config.json") as config_file:
            self.config = json.load(config_file)

        # State Management
        self.state = ProgramState()
        self.state.program_start_time = time.time()

        # Submodules
        self.project_manager = ProjectManager(self.config, self.state)
        self.ui_display = UIDisplay(self.config, self.state)
        self.camcap = CameraCapture(self.config, self.state)

        # Timing and Playback controls
        self.last_capture_time = self.state.program_start_time - self.config["capture_interval"]
        self.state.last_keypress = time.time()

        # Initialize Project and State
        self.read_log_file()
        self.project_manager.setup()
        self.write_log_file()

    def read_log_file(self):
        """Reads the log file to resume the last session's state."""
        try:
            with open(self.LOG_PATH, "r") as log_file:
                self.state.projectName_record = log_file.readline().strip()
                self.state.imgIndex_record = int(log_file.readline().strip())
                self.state.program_start_time = float(log_file.readline().strip())
        except FileNotFoundError:
            print("Log file not found. Starting with default values.")

    def write_log_file(self):
        """Writes the current state to the log file."""
        with open(self.LOG_PATH, "w") as log_file:
            log_file.write(f"{self.state.projectName_record}\n{self.state.imgIndex_record}\n{self.state.program_start_time}")

    def handle_key_press(self):
        """Handles key press events for playback control."""
        key = self.state.key
        if key in [ord('d'), ord('a')]:
            self.state.last_keypress = time.time()
            self.state.default = False
            direction = -1 if key == ord('a') else 1
            self.state.playback_speed = self.config["playback_speeds"][self.state.playback_speed_index] * direction
            self.state.image_step = self.config["image_step"][self.state.playback_speed_index] * direction
            self.state.playback_speed_index = (self.state.playback_speed_index + 1) % len(self.config["playback_speeds"])
        elif key == ord('s'):  # Pause/Play
            self.state.last_keypress = time.time()
            self.state.default = False
            self.state.playback_speed = 1 if self.state.playback_speed > 0 else -1
            self.state.image_step = 1 if self.state.playback_speed > 0 else -1

        elif key in [ord('e'), ord('w')]:  # Select Project
            self.state.last_keypress = time.time()
            self.state.default = False
            step = 1 if key == ord('e') else -1
            self.state.projectName_display_index = (self.state.projectName_display_index + step) % len(self.state.projects)
            self.state.projectName_display = self.state.projects[self.state.projectName_display_index]
            self.state.imgIndex_display = 1
            self.state.imgMaxIndex_display = self.state.projects_dict[self.state.projectName_display]['max_index']
            self.state.imgIndices_display = self.state.projects_dict[self.state.projectName_display]['indices']
            print(f"Selected project: {self.state.projectName_display}")
            self.state.baseUrl_display = os.path.join(self.config["projects_folder"],
                                                       self.state.projectName_display,
                                                       self.state.img_file_prefix)

        elif key == 27:  # ESC key
            print("Quitting program.")
            return False

        return True

    def main_loop(self):
        """Main loop for capturing images and handling playback."""
        while True:
            if not self.handle_key_press():
                break

            # Capture Image
            if self.config["capture"] and time.time() - self.last_capture_time >= self.config["capture_interval"]:
                elapsed_time = int(time.time() - self.state.program_start_time)
                self.camcap.capture_image(elapsed_time)
                self.last_capture_time = time.time()

                if self.state.projectName_display == self.state.projectName_record:
                    self.state.imgMaxIndex_display += 1
                self.state.imgIndex_record += 1
                self.write_log_file()

            # Playback
            self.ui_display.play_movie()
            if not self.state.default:
                self.ui_display.return_to_default()


    def cleanup(self):
        """Cleans up resources."""
        self.camcap.cleanup()
        self.ui_display.cleanup()


if __name__ == "__main__":
    timelapse = TimeLapse()
    print("Configuration Loaded:")
    print(timelapse.config)
    try:
        timelapse.main_loop()
    finally:
        timelapse.cleanup()