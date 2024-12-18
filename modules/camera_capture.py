import cv2

class CameraCapture:
    """Handles camera initialization and image capturing."""

    def __init__(self, config, state):
        """Initializes camera settings."""
        self.config = config
        self.state = state
        self.cap = self.initialize_camera()

    def initialize_camera(self, device_number=0):
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

    def capture_image(self, elapsed_time):
        """Captures an image and saves it with a timestamp."""
        if not self.cap:
            print("Error: Camera not initialized.")
            return

        ret, frame = self.cap.read()
        if ret:
            img_path = f"{self.state.baseUrl_record}{self.state.imgIndex_record}.jpg"
            self.save_image_with_timestamp(frame, img_path, elapsed_time)
            print(f"Image saved: {img_path}")
        else:
            print("Error: Failed to capture image.")

    def save_image_with_timestamp(self, frame, img_path, elapsed_time):
        """Saves an image with a time overlay encoded in pixel values."""
        stats = self._map_time_to_pixel_values(elapsed_time)
        pix_range = self.config["pixels_for_timestamp"]

        # Overlay the time in the pixel grid
        frame[0:pix_range, 0:pix_range] = stats[0]
        frame[pix_range:2*pix_range, 0:pix_range] = stats[1]
        frame[0:pix_range, pix_range:2*pix_range] = stats[1]
        frame[2*pix_range:3*pix_range, 0:pix_range] = stats[2]
        frame[0:pix_range, 2*pix_range:3*pix_range] = stats[2]
        frame[3*pix_range:4*pix_range, 0:pix_range] = stats[3]
        frame[0:pix_range, 3*pix_range:4*pix_range] = stats[3]

        # Save the image with specified quality
        cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

    def _map_time_to_pixel_values(self, elapsed_time):
        """Maps elapsed time to pixel intensity values."""
        days = elapsed_time // 86400
        hours = (elapsed_time % 86400) // 3600
        minutes = (elapsed_time % 3600) // 60
        seconds = elapsed_time % 60
        return [
            days * 10 + 4, 
            hours * 10 + 4, 
            minutes * 4 + 2, 
            seconds * 4 + 2
        ]

    def cleanup(self):
        """Releases the camera resource."""
        if self.cap:
            self.cap.release()
            print("Camera resources released.")