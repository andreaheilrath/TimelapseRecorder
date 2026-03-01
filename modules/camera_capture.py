import cv2
from typing import Any

class CameraCapture:
    """Handles camera initialization and image capturing."""
    JPEG_QUALITY = 80
    SECONDS_PER_DAY = 86400
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_MINUTE = 60
    DAY_HOUR_SCALE = 10
    MINUTE_SECOND_SCALE = 4
    DAY_HOUR_OFFSET = 4
    MINUTE_SECOND_OFFSET = 2

    def __init__(self, config: dict[str, Any], state: Any) -> None:
        """Initializes camera settings."""
        self.config = config
        self.state = state
        self.cap = self.initialize_camera()

    def initialize_camera(self, device_number: int = 0) -> cv2.VideoCapture:
        """Initializes the camera with the configured settings."""
        if self.config["on_raspberry"]:
            cap = cv2.VideoCapture(device_number, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(device_number)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["height"])
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        if not cap.isOpened():
            print("Error: Camera failed to initialize.")
        else:
            print("Camera successfully initialized.")

        return cap

    def capture_image(self, elapsed_time: int) -> bool:
        """Captures an image and saves it with a timestamp."""
        if not self.cap or not self.cap.isOpened():
            print("Error: Camera not initialized.")
            return False

        ret, frame = self.cap.read()
        if ret:
            img_path = f"{self.state.base_url_record}{self.state.img_index_record}.jpg"
            self.save_image_with_timestamp(frame, img_path, elapsed_time)
            print(f"Image saved: {img_path}")
            return True
        else:
            print("Error: Failed to capture image.")
            return False

    def save_image_with_timestamp(self, frame: Any, img_path: str, elapsed_time: int) -> None:
        """Saves an image with a time overlay encoded in pixel values."""
        stats = self._map_time_to_pixel_values(elapsed_time)
        pixel_range = self.config["pixels_for_timestamp"]

        # Overlay the time in the pixel grid
        frame[0:pixel_range, 0:pixel_range] = stats[0]
        frame[pixel_range:2 * pixel_range, 0:pixel_range] = stats[1]
        frame[0:pixel_range, pixel_range:2 * pixel_range] = stats[1]
        frame[2 * pixel_range:3 * pixel_range, 0:pixel_range] = stats[2]
        frame[0:pixel_range, 2 * pixel_range:3 * pixel_range] = stats[2]
        frame[3 * pixel_range:4 * pixel_range, 0:pixel_range] = stats[3]
        frame[0:pixel_range, 3 * pixel_range:4 * pixel_range] = stats[3]

        # Save the image with specified quality
        cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, self.JPEG_QUALITY])

    def _map_time_to_pixel_values(self, elapsed_time: int) -> list[int]:
        """Maps elapsed time to pixel intensity values."""
        days = elapsed_time // self.SECONDS_PER_DAY
        hours = (elapsed_time % self.SECONDS_PER_DAY) // self.SECONDS_PER_HOUR
        minutes = (elapsed_time % self.SECONDS_PER_HOUR) // self.SECONDS_PER_MINUTE
        seconds = elapsed_time % self.SECONDS_PER_MINUTE
        return [
            days * self.DAY_HOUR_SCALE + self.DAY_HOUR_OFFSET,
            hours * self.DAY_HOUR_SCALE + self.DAY_HOUR_OFFSET,
            minutes * self.MINUTE_SECOND_SCALE + self.MINUTE_SECOND_OFFSET,
            seconds * self.MINUTE_SECOND_SCALE + self.MINUTE_SECOND_OFFSET
        ]

    def cleanup(self) -> None:
        """Releases the camera resource."""
        if self.cap:
            self.cap.release()
            print("Camera resources released.")
