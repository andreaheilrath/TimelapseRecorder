import json
import time
from typing import Any

from modules.camera_capture import CameraCapture
from modules.program_state import ProgramState
from modules.project_manager import ProjectManager
from modules.ui_display import UIDisplay


class TimeLapse:
    """A class for creating time-lapse videos using a connected camera."""

    LOG_PATH = "log.txt"
    CONFIG_PATH = "config.json"

    KEY_FORWARD = ord("d")
    KEY_BACKWARD = ord("a")
    KEY_PAUSE = ord("s")
    KEY_NEXT_PROJECT = ord("e")
    KEY_PREV_PROJECT = ord("w")
    KEY_ESCAPE = 27

    REQUIRED_CONFIG_KEYS = {
        "width",
        "height",
        "fullscreen",
        "landscape",
        "on_raspberry",
        "capture",
        "capture_interval",
        "pixels_for_timestamp",
        "default_playback_speed_index",
        "playback_speeds",
        "image_step",
        "projects_folder",
        "default_project",
        "default_display",
    }

    def __init__(self) -> None:
        # Load and validate configuration
        with open(self.CONFIG_PATH, "r", encoding="utf-8") as config_file:
            self.config: dict[str, Any] = json.load(config_file)
        self._validate_config()

        # State management
        self.state = ProgramState()
        self.state.program_start_time = time.time()

        # Submodules
        self.project_manager = ProjectManager(self.config, self.state)
        self.ui_display = UIDisplay(self.config, self.state)
        self.camera_capture = CameraCapture(self.config, self.state)

        # Timing and playback controls
        self.last_capture_time = self.state.program_start_time - self.config["capture_interval"]
        self.state.last_keypress = time.time()

        # Initialize project and state
        self.read_log_file()
        self.project_manager.setup()
        self.write_log_file()

    def _validate_config(self) -> None:
        missing_keys = self.REQUIRED_CONFIG_KEYS.difference(self.config)
        if missing_keys:
            missing_keys_sorted = ", ".join(sorted(missing_keys))
            raise ValueError(f"Missing config keys: {missing_keys_sorted}")

        if self.config["width"] <= 0 or self.config["height"] <= 0:
            raise ValueError("Config values 'width' and 'height' must be positive integers")
        if self.config["capture_interval"] <= 0:
            raise ValueError("Config value 'capture_interval' must be > 0")
        if self.config["pixels_for_timestamp"] <= 0:
            raise ValueError("Config value 'pixels_for_timestamp' must be > 0")

        playback_speeds = self.config["playback_speeds"]
        image_steps = self.config["image_step"]
        default_speed_index = self.config["default_playback_speed_index"]

        if not isinstance(playback_speeds, list) or not playback_speeds:
            raise ValueError("Config value 'playback_speeds' must be a non-empty list")
        if not isinstance(image_steps, list) or not image_steps:
            raise ValueError("Config value 'image_step' must be a non-empty list")
        if len(playback_speeds) != len(image_steps):
            raise ValueError("Config lists 'playback_speeds' and 'image_step' must have the same length")
        if default_speed_index < 0 or default_speed_index >= len(playback_speeds):
            raise ValueError("Config value 'default_playback_speed_index' is out of range")

    def _project_image_base_path(self, project_name: str) -> str:
        return self.project_manager.project_image_base_path(project_name)

    def read_log_file(self) -> None:
        """Reads the log file to resume the last session's state."""
        try:
            with open(self.LOG_PATH, "r", encoding="utf-8") as log_file:
                project_name = log_file.readline().strip()
                self.state.project_name_record = project_name or None
                self.state.img_index_record = int(log_file.readline().strip())
                self.state.program_start_time = float(log_file.readline().strip())
        except (FileNotFoundError, ValueError):
            print("Log file missing or invalid. Starting with default values.")

    def write_log_file(self) -> None:
        """Writes the current state to the log file."""
        with open(self.LOG_PATH, "w", encoding="utf-8") as log_file:
            log_file.write(
                f"{self.state.project_name_record}\n"
                f"{self.state.img_index_record}\n"
                f"{self.state.program_start_time}"
            )

    def handle_key_press(self) -> bool:
        """Handles key press events for playback control."""
        key = self.state.key
        if key in [self.KEY_FORWARD, self.KEY_BACKWARD]:
            self.state.last_keypress = time.time()
            self.state.is_default_mode = False
            direction = -1 if key == self.KEY_BACKWARD else 1
            self.state.playback_speed = self.config["playback_speeds"][self.state.playback_speed_index] * direction
            self.state.image_step = self.config["image_step"][self.state.playback_speed_index] * direction
            self.state.playback_speed_index = (self.state.playback_speed_index + 1) % len(self.config["playback_speeds"])
        elif key == self.KEY_PAUSE:  # Pause/Play
            self.state.last_keypress = time.time()
            self.state.is_default_mode = False
            self.state.playback_speed = 1 if self.state.playback_speed > 0 else -1
            self.state.image_step = 1 if self.state.playback_speed > 0 else -1
        elif key in [self.KEY_NEXT_PROJECT, self.KEY_PREV_PROJECT]:  # Select Project
            self.state.last_keypress = time.time()
            self.state.is_default_mode = False
            step = 1 if key == self.KEY_NEXT_PROJECT else -1
            self.state.project_name_display_index = (
                self.state.project_name_display_index + step
            ) % len(self.state.projects)
            self.state.project_name_display = self.state.projects[self.state.project_name_display_index]
            self.state.img_index_display = -1
            self.state.img_indices_display = self.state.projects_dict[self.state.project_name_display]["indices"]
            self.state.img_max_index_display = len(self.state.img_indices_display)
            print(f"Selected project: {self.state.project_name_display}")
            self.state.base_url_display = self._project_image_base_path(self.state.project_name_display)
        elif key == self.KEY_ESCAPE:
            print("Quitting program.")
            return False

        return True

    def main_loop(self) -> None:
        """Main loop for capturing images and handling playback."""
        while True:
            if not self.handle_key_press():
                break

            # Capture image
            if self.config["capture"] and time.time() - self.last_capture_time >= self.config["capture_interval"]:
                elapsed_time = int(time.time() - self.state.program_start_time)
                saved = self.camera_capture.capture_image(elapsed_time)
                if saved:
                    captured_index = self.state.img_index_record
                    if captured_index not in self.state.img_indices_record:
                        self.state.img_indices_record.append(captured_index)

                    record_project = self.state.project_name_record
                    self.state.projects_dict[record_project]["max_index"] = len(self.state.img_indices_record)

                    if self.state.project_name_display == record_project:
                        if (
                            self.state.img_indices_display is not self.state.img_indices_record
                            and captured_index not in self.state.img_indices_display
                        ):
                            self.state.img_indices_display.append(captured_index)
                        self.state.img_max_index_display = len(self.state.img_indices_display)

                    self.state.img_index_record += 1
                    self.write_log_file()

                self.last_capture_time = time.time()

            # Playback
            self.ui_display.play_movie()
            if not self.state.is_default_mode:
                self.ui_display.return_to_default()

    def cleanup(self) -> None:
        """Cleans up resources."""
        self.camera_capture.cleanup()
        self.ui_display.cleanup()


if __name__ == "__main__":
    timelapse = TimeLapse()
    print("Configuration Loaded:")
    print(timelapse.config)
    try:
        timelapse.main_loop()
    finally:
        timelapse.cleanup()
