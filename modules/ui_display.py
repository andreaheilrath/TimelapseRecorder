import cv2
import time
import numpy as np
from typing import Any

class UIDisplay:
    """Handles the user interface display for time-lapse playback."""
    MIN_FRAME_DELAY_MS = 46.87
    INACTIVITY_TIMEOUT_SECONDS = 120
    UI_BAR_HEIGHT = 60
    TIME_DIVISOR_DAYS_HOURS = 10
    TIME_DIVISOR_MINUTES_SECONDS = 4

    def __init__(self, config: dict[str, Any], state: Any) -> None:
        """Initializes the UI display."""
        self.window_name = "Time Lapse"
        self.config = config
        self.state = state

        # OpenCV window setup
        cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
        if self.config["fullscreen"]:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Initialize playback speed and step
        self.state.playback_speed = self.config["playback_speeds"][self.config["default_playback_speed_index"]]
        self.state.image_step = self.config["image_step"][self.config["default_playback_speed_index"]]

    def play_movie(self) -> None:
        """Plays the captured images as a time-lapse movie."""
        total_images = len(self.state.img_indices_display)

        if total_images > 0:
            self.state.img_index_display = (self.state.img_index_display + self.state.image_step) % total_images
            self.update_display(self.state.img_index_display)

        # Adjust time delay based on playback speed.
        time_delta = max(self.MIN_FRAME_DELAY_MS, 1000 * self.config["capture_interval"] / abs(self.state.playback_speed))
        self.state.key = cv2.waitKey(int(time_delta))

    def return_to_default(self) -> None:
        """Returns playback settings to default after inactivity."""
        delta = time.time() - self.state.last_keypress
        if delta > self.INACTIVITY_TIMEOUT_SECONDS:
            self.state.project_name_display = self.state.project_name_record
            if self.state.project_name_display in self.state.projects:
                self.state.project_name_display_index = self.state.projects.index(self.state.project_name_display)
            self.state.base_url_display = self.state.base_url_record
            self.state.img_indices_display = self.state.img_indices_record
            self.state.img_max_index_display = len(self.state.img_indices_display)
            self.state.img_index_display = -1
            self.state.playback_speed = self.config["playback_speeds"][self.config["default_playback_speed_index"]]
            self.state.image_step = self.config["image_step"][self.config["default_playback_speed_index"]]
            self.state.is_default_mode = True
            print("Returning to Default")

    def update_display(self, index: int) -> None:
        """Displays the image at the given index with overlays."""
        if not self.state.img_indices_display:
            return
        if index < 0 or index >= len(self.state.img_indices_display):
            return

        retrieved_index = self.state.img_indices_display[index]
        img_filename = f"{self.state.base_url_display}{retrieved_index}.jpg"
        frame = cv2.imread(img_filename)

        if frame is not None:
            ui_element = self._generate_ui_element(frame)
            frame = self._add_ui_overlay(frame, ui_element)
            cv2.imshow(self.window_name, frame)

    def _generate_ui_element(self, frame: Any) -> Any:
        """Generates the overlay UI element with elapsed time and playback info."""
        font_specs = {
            'fontFace': cv2.FONT_HERSHEY_DUPLEX,
            'fontScale': 1.2,
            'color': (255, 255, 255),
            'thickness': 1
        }

        # Create a black background for text
        height = self.UI_BAR_HEIGHT
        width = self.config["width"] if self.config["landscape"] else self.config["height"]
        ui_element = np.zeros((height, width, 3), np.uint8)

        # Map elapsed time from image pixels
        pix = self.config["pixels_for_timestamp"]
        value_days = int(frame[pix // 2, pix // 2].mean())
        value_hours = int(frame[pix + pix // 2, pix // 2].mean())
        value_minutes = int(frame[2 * pix + pix // 2, pix // 2].mean())
        value_seconds = int(frame[3 * pix + pix // 2, pix // 2].mean())
        elapsed_time = self.map_255_time([value_days, value_hours, value_minutes, value_seconds])

        # Print elapsed time
        space = 120
        left_space = 30
        self._put_text(ui_element, f"{elapsed_time[0]}d", (left_space, 40), font_specs)
        self._put_text(ui_element, f"{elapsed_time[1]}h", (left_space + space, 40), font_specs)
        self._put_text(ui_element, f"{elapsed_time[2]}m", (left_space + 2 * space, 40), font_specs)
        self._put_text(ui_element, f"{elapsed_time[3]}s", (left_space + 3 * space, 40), font_specs)

        # Print playback speed
        icon = ">>" if self.state.playback_speed > 1 else "<<" if self.state.playback_speed < -1 else "> "
        self._put_text(ui_element, f"{icon}{abs(self.state.playback_speed)}x", (width // 2, 40), font_specs)

        # Print project name
        self._put_text(ui_element, self.state.project_name_display, (6 * width // 8, 40), font_specs)

        return ui_element

    def _add_ui_overlay(self, frame: Any, ui_element: Any) -> Any:
        """Adds the UI overlay to the frame."""
        if self.config["landscape"]:
            frame[0:self.UI_BAR_HEIGHT, self.config["pixels_for_timestamp"]:] = ui_element[:, self.config["pixels_for_timestamp"]:]
        else:
            ui_element = cv2.rotate(ui_element, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame[self.config["pixels_for_timestamp"]:, 0:self.UI_BAR_HEIGHT] = ui_element
        return frame

    def _put_text(self, canvas: Any, text: str, position: tuple[int, int], font_specs: dict[str, Any]) -> None:
        """Draws text on a canvas with given font specifications."""
        cv2.putText(canvas, text, position, font_specs["fontFace"], font_specs["fontScale"], font_specs["color"], font_specs["thickness"])

    def map_255_time(self, stats: list[int]) -> list[int]:
        """Converts pixel intensity values back to time units."""
        return [
            stats[0] // self.TIME_DIVISOR_DAYS_HOURS,
            stats[1] // self.TIME_DIVISOR_DAYS_HOURS,
            stats[2] // self.TIME_DIVISOR_MINUTES_SECONDS,
            stats[3] // self.TIME_DIVISOR_MINUTES_SECONDS,
        ]

    def cleanup(self) -> None:
        """Cleans up OpenCV windows."""
        cv2.destroyAllWindows()
