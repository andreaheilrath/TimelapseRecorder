import cv2
import time
import os
import numpy as np
from typing import Any

class UIDisplay:
    """Handles the user interface display for time-lapse playback."""
    TARGET_FPS = 30
    FRAME_DELAY_MS = int(1000 / TARGET_FPS)
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
        default_index = self.config["default_playback_speed_index"]
        self.state.playback_speed = self.config["playback_speeds"][default_index]

    def play_movie(self) -> None:
        """Plays the captured images as a time-lapse movie."""
        total_images = len(self.state.img_indices_display)

        if total_images > 0 and self.state.is_paused:
            if self.state.img_index_display < 0:
                self.state.img_index_display = 0
            self.update_display(self.state.img_index_display)
            self.state.key = cv2.waitKey(self.FRAME_DELAY_MS)
            return

        if total_images > 0:
            if self.state.img_index_display < 0:
                self.state.img_index_display = 0

            frame_delta_seconds = max(1e-6, self.state.display_frame_delta_seconds)
            frames_per_tick = (
                self.state.playback_speed
                * (1.0 / self.TARGET_FPS)
                / frame_delta_seconds
            )
            self.state.frame_advance_accumulator += frames_per_tick
            frame_step = int(self.state.frame_advance_accumulator)
            if frame_step != 0:
                self.state.frame_advance_accumulator -= frame_step
                self.state.img_index_display = (self.state.img_index_display + frame_step) % total_images
            self.update_display(self.state.img_index_display)

        self.state.key = cv2.waitKey(self.FRAME_DELAY_MS)

    def return_to_default(self) -> None:
        """Returns playback settings to default after inactivity."""
        delta = time.time() - self.state.last_keypress
        if delta <= self.INACTIVITY_TIMEOUT_SECONDS:
            return

        current_project = self.state.project_name_display
        default_display = self.config.get("default_display")
        target_project = default_display if default_display in self.state.projects else current_project

        if self.state.is_default_mode and current_project == target_project:
            return

        if target_project in self.state.projects:
            self.state.project_name_display = target_project
            self.state.project_name_display_index = self.state.projects.index(self.state.project_name_display)
            self.state.base_url_display = os.path.join(
                self.config["projects_folder"],
                self.state.project_name_display,
                self.state.img_file_prefix,
            )
            self.state.img_indices_display = self.state.projects_dict[self.state.project_name_display]["indices"]

        self.state.img_index_display = -1
        self.state.display_frame_delta_seconds = self.state.projects_dict[self.state.project_name_display]["frame_delta_seconds"]
        self.state.frame_advance_accumulator = 0.0
        default_index = self.config["default_playback_speed_index"]
        self.state.playback_speed = self.config["playback_speeds"][default_index]
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
        space = 100
        left_space = 20
        self._put_text(ui_element, f"{elapsed_time[0]:02d}d", (left_space, 40), font_specs)
        self._put_text(ui_element, f"{elapsed_time[1]:02d}h", (left_space + space, 40), font_specs)
        self._put_text(ui_element, f"{elapsed_time[2]:02d}m", (left_space + 2 * space, 40), font_specs)
        self._put_text(ui_element, f"{elapsed_time[3]:02d}s", (left_space + 3 * space, 40), font_specs)

        # Print playback speed
        icon = ">>" if self.state.playback_speed > 1 else "<<" if self.state.playback_speed < -1 else "> "
        self._put_text(ui_element, f"{icon}{abs(self.state.playback_speed)}x", (4 * width // 10, 40), font_specs)

        # Print project name
        self._put_text(ui_element, self.state.project_name_display, (2 * width // 3, 40), font_specs)

        return ui_element

    def _add_ui_overlay(self, frame: Any, ui_element: Any) -> Any:
        """Adds the UI overlay to the frame."""
        pixel_offset = self.config["pixels_for_timestamp"]
        if self.config["landscape"]:
            target_height = min(self.UI_BAR_HEIGHT, frame.shape[0], ui_element.shape[0])
            target_width = min(frame.shape[1] - pixel_offset, ui_element.shape[1] - pixel_offset)
            if target_height > 0 and target_width > 0:
                frame[0:target_height, pixel_offset:pixel_offset + target_width] = ui_element[
                    0:target_height, pixel_offset:pixel_offset + target_width
                ]
        else:
            ui_element = cv2.rotate(ui_element, cv2.ROTATE_90_COUNTERCLOCKWISE)
            target_height = min(frame.shape[0] - pixel_offset, ui_element.shape[0] - pixel_offset)
            target_width = min(self.UI_BAR_HEIGHT, frame.shape[1], ui_element.shape[1])
            if target_height > 0 and target_width > 0:
                frame[pixel_offset:pixel_offset + target_height, 0:target_width] = ui_element[
                    pixel_offset:pixel_offset + target_height, 0:target_width
                ]
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
