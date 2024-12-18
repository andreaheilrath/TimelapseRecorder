import cv2
import time
import numpy as np

class UIDisplay:
    """Handles the user interface display for time-lapse playback."""

    def __init__(self, config, state):
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

    def play_movie(self):
        """Plays the captured images as a time-lapse movie."""
        if self.state.img_max_index > 0:
            self.state.img_shown_index = (self.state.img_shown_index + self.state.image_step) % self.state.img_max_index
        else:
            self.state.img_shown_index = 0

        # Update the display
        self.update_display(self.state.img_shown_index)

        # Adjust time delay based on playback speed
        time_delta = max(46.87, 1000 * self.config["capture_interval"] / abs(self.state.playback_speed))
        self.state.key = cv2.waitKey(int(time_delta))

    def return_to_default(self):
        """Returns playback settings to default after inactivity."""
        delta = time.time() - self.state.last_keypress
        if delta > 120:
            self.state.selected_project = self.state.active_project
            self.state.playback_speed = self.config["playback_speeds"][self.config["default_playback_speed_index"]]
            self.state.image_step = self.config["image_step"][self.config["default_playback_speed_index"]]
            self.state.default = True
            print("Returning to Default")

    def update_display(self, index):
        """Displays the image at the given index with overlays."""
        img_filename = f"{self.state.base_url_display}{index}.jpg"
        frame = cv2.imread(img_filename)

        if frame is not None:
            ui_element = self._generate_ui_element(frame)
            frame = self._add_ui_overlay(frame, ui_element)
            cv2.imshow(self.window_name, frame)

    def _generate_ui_element(self, frame):
        """Generates the overlay UI element with elapsed time and playback info."""
        font_specs = {
            'fontFace': cv2.FONT_HERSHEY_DUPLEX,
            'fontScale': 1.2,
            'color': (255, 255, 255),
            'thickness': 1
        }

        # Create a black background for text
        height, width = 60, self.config["width"] if self.config["landscape"] else self.config["height"]
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
        self._put_text(ui_element, self.state.selected_project, (6 * width // 8, 40), font_specs)

        return ui_element

    def _add_ui_overlay(self, frame, ui_element):
        """Adds the UI overlay to the frame."""
        if self.config["landscape"]:
            frame[0:60, self.config["pixels_for_timestamp"]:] = ui_element[:, self.config["pixels_for_timestamp"]:]
        else:
            ui_element = cv2.rotate(ui_element, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame[self.config["pixels_for_timestamp"]:, 0:60] = ui_element
        return frame

    def _put_text(self, canvas, text, position, font_specs):
        """Draws text on a canvas with given font specifications."""
        cv2.putText(canvas, text, position, font_specs["fontFace"], font_specs["fontScale"], font_specs["color"], font_specs["thickness"])

    def map_255_time(self, stats):
        """Converts pixel intensity values back to time units."""
        return [stats[0] // 10, stats[1] // 10, stats[2] // 4, stats[3] // 4]

    def cleanup(self):
        """Cleans up OpenCV windows."""
        cv2.destroyAllWindows()