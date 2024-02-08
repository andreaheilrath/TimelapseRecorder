import cv2
import time
import os
import logging

class TimeLapseCamera:
    """A class for creating time-lapse videos using a connected camera."""
    
    # Constants
    CAPTURE_INTERVAL = 5  # Interval between image captures in seconds
    DEFAULT_PLAYBACK_SPEED = 1.0  # Default playback speed when reviewing images
    LOG_PATH = "log.txt"  # Path to the log file
    PROJECTS_FOLDER = "projects"  # Folder where project images are stored
    DEFAULT_PROJECT = "test"  # Default project name
    PLAYBACK_SPEEDS = [16., 32., 64., 128.]  # Playback speeds for reviewing images
    WINDOW_NAME = "Zeitmaschine"  # Window name for the display

    def __init__(self):
        """Initializes the TimeLapseCamera object."""
        # Camera and image tracking
        self.cap = None
        self.current_project = ""
        self.img_file_prefix = "image_"
        self.img_index = 1
        
        # Playback controls
        self.img_shown_index = 1
        self.key = None
        self.playback_speed = self.DEFAULT_PLAYBACK_SPEED
        self.playback_speed_index = 0
        
        # Timing
        self.program_start_time = time.time()
        self.last_picture_time = self.program_start_time - self.CAPTURE_INTERVAL
        
        # Logging
        logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

    def initialize(self):
        """Initializes the camera and project settings."""
        if not self.initialize_camera():
            logging.error("Failed to initialize camera. Exiting.")
            exit(1)
        self.setup_project()
        self.prepare_display()

    def initialize_camera(self):
        """Attempts to initialize the camera."""
        self.cap = cv2.VideoCapture(0)
        return self.cap.isOpened()

    def setup_project(self):
        """Sets up the project directory and reads the last state from the log file."""
        self.read_log_file()
        self.ensure_directory_exists(self.PROJECTS_FOLDER)
        projects = self.get_projects()
        self.select_project(projects)
        self.img_file_prefix = os.path.join(self.current_project, self.img_file_prefix)
        print(f"Project: {self.current_project} | Current Image Index: {self.img_index}")
        logging.info(f"Project: {self.current_project} | Current Image Index: {self.img_index}")

    def prepare_display(self):
        """Prepares the display window for showing images."""
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_GUI_NORMAL)
        cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def read_log_file(self):
        """Reads the log file to resume the last session's state."""
        try:
            with open(self.LOG_PATH, "r") as log_file:
                self.current_project = log_file.readline().strip()
                self.img_index = int(log_file.readline().strip())
        except FileNotFoundError:
            logging.info("Log file not found. Starting with default values.")

    def write_log_file(self):
        """Writes the current state to the log file."""
        with open(self.LOG_PATH, "w") as log_file:
            log_file.write(f"{self.current_project}\n{self.img_index}")

    def ensure_directory_exists(self, path):
        """Ensures that a directory exists at the given path."""
        os.makedirs(path, exist_ok=True)

    def get_projects(self):
        """Returns a list of projects sorted by creation time."""
        projects = [d for d in os.listdir(self.PROJECTS_FOLDER) if os.path.isdir(os.path.join(self.PROJECTS_FOLDER, d))]
        projects.sort(key=lambda d: os.path.getctime(os.path.join(self.PROJECTS_FOLDER, d)))
        if not projects:
            projects.append(self.DEFAULT_PROJECT)
            self.ensure_directory_exists(os.path.join(self.PROJECTS_FOLDER, self.DEFAULT_PROJECT))
        return projects

    def select_project(self, projects):
        """Selects the current project from the available projects."""
        for project in projects:
            if self.is_directory_empty(os.path.join(self.PROJECTS_FOLDER, project)):
                self.current_project = project
                self.img_index = 1
                self.write_log_file()
                return
        if self.current_project in projects:
            return
        self.current_project = self.DEFAULT_PROJECT
        self.write_log_file()

    def is_directory_empty(self, path):
        """Checks if a directory is empty."""
        return next(os.scandir(path), None) is None

    def capture_image(self):
        """Captures an image from the camera and saves it with a timestamp."""
        if not self.cap:
            logging.error("Camera not initialized.")
            return
        ret, frame = self.cap.read()
        if ret:
            img_filename = f"{self.PROJECTS_FOLDER}/{self.img_file_prefix}{self.img_index}.jpg"
            self.save_image_with_timestamp(frame, img_filename)
            self.last_picture_time = time.time()
            self.img_index += 1
            self.write_log_file()

    def save_image_with_timestamp(self, frame, filename):
        """Saves the image with a timestamp overlay."""
        frame_with_timestamp = self.add_timestamp_to_image(frame)
        cv2.imwrite(filename, frame_with_timestamp)

    def add_timestamp_to_image(self, frame):
        """Adds a timestamp overlay to the given image frame."""
        elapsed_time = int(time.time() - self.program_start_time)
        timestamp_text = f"Elapsed Time: {elapsed_time // 3600:02d}:{(elapsed_time % 3600) // 60:02d}:{elapsed_time % 60:02d}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(timestamp_text, font, 0.5, 1)[0]
        frame = cv2.rectangle(frame, (0, 0), (text_size[0] + 10, text_size[1] + 10), (0, 0, 0), -1)
        cv2.putText(frame, timestamp_text, (5, text_size[1] + 5), font, 0.5, (255, 255, 255), 1)
        return frame

    def update_display(self, index):
        """Updates the display with the image at the given index."""
        img_filename = f"{self.PROJECTS_FOLDER}/{self.img_file_prefix}{index}.jpg"
        frame = cv2.imread(img_filename)
        if frame is not None:
            cv2.imshow(self.WINDOW_NAME, frame)

    def play_movie(self):
        """Plays the captured images as a time-lapse movie."""
        self.img_shown_index = (self.img_shown_index + (1 if self.playback_speed > 0 else -1)) % self.img_index
        self.update_display(self.img_shown_index)
        self.key = cv2.waitKey(int(1000 * self.CAPTURE_INTERVAL / abs(self.playback_speed)))

    def handle_key_press(self):
        """Handles key press events for playback control."""
        if self.key in [ord('f'), ord('b')]:
            self.playback_speed = self.PLAYBACK_SPEEDS[self.playback_speed_index] * (-1 if self.key == ord('b') else 1)
            self.playback_speed_index = (self.playback_speed_index + 1) % len(self.PLAYBACK_SPEEDS)
            direction = "backward" if self.key == ord('b') else "forward"
            logging.info(f"{direction} speed {self.playback_speed}")
        elif self.key == ord('p'):
            self.playback_speed = self.DEFAULT_PLAYBACK_SPEED
            logging.info("Play/Pause")
        elif self.key == ord('q'):
            logging.info("Quit")
            return False
        return True

    def main_loop(self):
        """Main loop for capturing images and handling playback."""
        while True:
            if not self.handle_key_press():
                break
            if time.time() - self.last_picture_time >= self.CAPTURE_INTERVAL:
                self.capture_image()
            self.play_movie()

    def cleanup(self):
        """Releases resources and cleans up before exiting."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    cam = TimeLapseCamera()
    cam.initialize()
    cam.main_loop()
    cam.cleanup()