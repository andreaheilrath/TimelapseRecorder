import cv2
import time
import os

class TimeLapseCamera:
    CAPTURE_INTERVAL = 5  # Time between captures in seconds
    PLAYBACK_SPEED = 1.0  # Playback speed factor
    LOG_PATH = "log.txt"
    PROJECTS_FOLDER = "projects"
    DEFAULT_PROJECT = "test"
    PLAYBACK_SPEEDS = [16., 32., 64., 128.]  # Define your desired playback speeds here
    playback_speed_index = 0  # Index to keep track of the current playback speed


    def __init__(self):
        self.cap = None
        self.current_project = ""
        self.img_file_prefix = ""
        self.img_index = 0
        self.img_shown_index = 1
        self.last_picture_time = time.time()
        self.program_start_time = self.last_picture_time
        self.playback_speed = self.PLAYBACK_SPEED

    def initialize(self):
        if not self.initialize_camera():
            print("Failed to initialize camera. Exiting.")
            exit(1)
        self.setup_project()
        cv2.namedWindow("Zeitmaschine", cv2.WINDOW_NORMAL)

    def initialize_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            return False
        return True

    def setup_project(self):
        if not os.path.exists(self.LOG_PATH):
            with open(self.LOG_PATH, "w") as log:
                pass
        else:
            with open(self.LOG_PATH, "r") as log:
                self.current_project = log.readline().strip()
                self.img_index = int(log.readline().strip())

        if not os.path.exists(self.PROJECTS_FOLDER):
            os.makedirs(os.path.join(self.PROJECTS_FOLDER, self.DEFAULT_PROJECT))
            self.current_project = self.DEFAULT_PROJECT
            self.img_index = 0
        else:
            self.current_project = self.new_folder()

        self.img_file_prefix = os.path.join(self.current_project, "image_")
        print(f"Project: {self.current_project} | Current Image Index: {self.img_index}")

    def new_folder(self):
        project_paths = [os.path.join(self.PROJECTS_FOLDER, d) for d in os.listdir(self.PROJECTS_FOLDER) if os.path.isdir(os.path.join(self.PROJECTS_FOLDER, d))]
        if not project_paths:
            return self.DEFAULT_PROJECT
        latest_project_path = max(project_paths, key=os.path.getmtime)
        return os.path.basename(latest_project_path)

    def capture_image(self):
        if not self.cap:
            print("Camera not initialized.")
            return None

        ret, frame = self.cap.read()
        if ret:
            img_filename = f"{self.PROJECTS_FOLDER}/{self.img_file_prefix}{self.img_index}.jpg"
            self.save_image_with_timestamp(frame, img_filename)
            self.last_picture_time = time.time()
            self.img_index += 1

            with open(self.LOG_PATH, 'w') as log:
                log.write(f"{self.current_project}\n{self.img_index}")
        return frame

    def save_image_with_timestamp(self, frame, filename):
        frame_with_timestamp = self.add_timestamp_to_image(frame)
        try:
            cv2.imwrite(filename, frame_with_timestamp)
        except Exception as e:
            print(f"Failed to save image {filename}: {e}")

    def add_timestamp_to_image(self, frame):
        elapsed_time = int(time.time() - self.program_start_time)
        hours, minutes, seconds = elapsed_time // 3600, (elapsed_time % 3600) // 60, elapsed_time % 60
        text = f"Elapsed Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height) = cv2.getTextSize(text, font, 0.5, 1)[0]
        img = cv2.rectangle(frame, (0, 0), (text_width + 10, text_height + 10), (0, 0, 0), -1)
        img = cv2.putText(img, text, (5, text_height + 5), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return img

    def update_display(self, index):
        img_filename = f"{self.PROJECTS_FOLDER}/{self.img_file_prefix}{index}.jpg"
        frame = cv2.imread(img_filename)
        if frame is not None:
            cv2.imshow("Zeitmaschine", frame)

    def play_movie(self):
        self.img_shown_index += 1 if self.playback_speed > 0 else -1
        self.img_shown_index = (self.img_shown_index + self.img_index) % self.img_index
        self.update_display(self.img_shown_index)
        time.sleep(self.CAPTURE_INTERVAL / abs(self.playback_speed))


    def handle_key_press(self):
        key = cv2.waitKey(1)
        if key == ord('f'):
            self.playback_speed_index = (self.playback_speed_index + 1) % len(self.PLAYBACK_SPEEDS)
            self.playback_speed = self.PLAYBACK_SPEEDS[self.playback_speed_index]
            print(f"forward speed {self.playback_speed}")
        elif key == ord('b'):
            self.playback_speed_index = (self.playback_speed_index + 1) % len(self.PLAYBACK_SPEEDS)
            self.playback_speed = -1. * self.PLAYBACK_SPEEDS[self.playback_speed_index]
            print(f"backward speed {self.playback_speed}")
        elif key == ord('p'):
            self.playback_speed = 1
            print("play/pause")
        elif key == ord('q'):
            print("quit")
            return False
        return True

    def main_loop(self):
        while True:
            if not self.handle_key_press():
                break
            if time.time() - self.last_picture_time >= self.CAPTURE_INTERVAL:
                self.capture_image()
            self.play_movie()

    def cleanup(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    cam = TimeLapseCamera()
    cam.initialize()
    cam.main_loop()
    cam.cleanup()
