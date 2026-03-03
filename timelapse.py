import json
import time
from typing import Any
from pathlib import Path

from modules.camera_capture import CameraCapture
from modules.program_state import ProgramState
from modules.project_manager import ProjectManager
from modules.ui_display import UIDisplay


class TimeLapse:
    """A class for creating time-lapse videos using a connected camera."""

    BASE_DIR = Path(__file__).resolve().parent
    LOG_PATH = BASE_DIR / "log.txt"
    CONFIG_PATH = BASE_DIR / "config.json"

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
        "projects_folder",
        "default_project_name",
    }

    def __init__(self) -> None:
        # Load and validate configuration
        with open(self.CONFIG_PATH, "r", encoding="utf-8") as config_file:
            self.config: dict[str, Any] = json.load(config_file)
        self._normalize_paths()
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
        default_speed_index = self.config["default_playback_speed_index"]

        if not isinstance(playback_speeds, list) or not playback_speeds:
            raise ValueError("Config value 'playback_speeds' must be a non-empty list")
        if default_speed_index < 0 or default_speed_index >= len(playback_speeds):
            raise ValueError("Config value 'default_playback_speed_index' is out of range")

    def _normalize_paths(self) -> None:
        projects_folder = Path(self.config["projects_folder"])
        if not projects_folder.is_absolute():
            projects_folder = self.BASE_DIR / projects_folder
        self.config["projects_folder"] = str(projects_folder)

    def _project_image_base_path(self, project_name: str) -> str:
        return self.project_manager.project_image_base_path(project_name)

    def _change_playback_speed_level(self, direction: int) -> None:
        """Move one step in the speed ladder.

        Ladder order:
        negative max ... negative min ... positive min ... positive max
        direction +1: move right (triggered by 'd')
        direction -1: move left (triggered by 'a')
        """
        speeds = self.config["playback_speeds"]
        level_count = len(speeds)

        levels: list[tuple[int, int]] = []
        for abs_index in range(level_count - 1, -1, -1):
            levels.append((-speeds[abs_index], abs_index))
        for abs_index in range(level_count):
            levels.append((speeds[abs_index], abs_index))

        current_speed = self.state.playback_speed
        current_level_index = next(
            (idx for idx, (speed, _) in enumerate(levels) if speed == current_speed),
            None,
        )

        # If current speed is outside the configured ladder (e.g., +/-1 after pause),
        # snap to the closest directional boundary around zero.
        if current_level_index is None:
            target_level_index = level_count if direction > 0 else level_count - 1
            new_speed, _ = levels[target_level_index]
            self.state.playback_speed = new_speed
            return

        new_level_index = max(0, min(len(levels) - 1, current_level_index + direction))
        if new_level_index == current_level_index:
            return

        new_speed, _ = levels[new_level_index]
        self.state.playback_speed = new_speed

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
        if key == self.KEY_FORWARD:
            self.state.last_keypress = time.time()
            self.state.is_default_mode = False
            self._change_playback_speed_level(direction=1)
        elif key == self.KEY_BACKWARD:
            self.state.last_keypress = time.time()
            self.state.is_default_mode = False
            self._change_playback_speed_level(direction=-1)
        elif key == self.KEY_PAUSE:  # Pause/Play
            self.state.last_keypress = time.time()
            self.state.is_default_mode = False
            self.state.is_paused = not self.state.is_paused
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
            self.state.display_frame_delta_seconds = self.state.projects_dict[self.state.project_name_display]["frame_delta_seconds"]
            self.state.frame_advance_accumulator = 0.0
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

                    if self.state.project_name_display == self.state.project_name_record:
                        if (
                            self.state.img_indices_display is not self.state.img_indices_record
                            and captured_index not in self.state.img_indices_display
                        ):
                            self.state.img_indices_display.append(captured_index)

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
