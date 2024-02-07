import cv2
import time
import os


# Global Variables
cap = None
img_file_prefix = ""
img_index = 0
img_shown_index = 0
last_picture_time = 0
last_pressed_time = 0
delta_time = 5
state = ""
program_start_time = 0
current_project = None
projects_folder = "projects"
playback_speed = 1.0 


def new_folder(parent_folder = projects_folder):
    # Check if the parent folder exists
    if not os.path.exists(parent_folder):
        print(f"The parent folder '{parent_folder}' does not exist.")
        return None  # Or handle it in some other way
    # Iterate through all subfolders
    for folder_name in os.listdir(parent_folder):
        folder_path = os.path.join(parent_folder, folder_name)
        if os.path.isdir(folder_path) and not os.listdir(folder_path):
            return folder_name


def initialize():
    global cap, last_picture_time, last_pressed_time, program_start_time, img_index, current_project, img_file_prefix
    cap = cv2.VideoCapture(0)
    last_picture_time = time.time()
    last_pressed_time = time.time()
    program_start_time = time.time()
    if (new_folder()):
        current_project = new_folder()
        img_index = 0
        print("Started new project!")
    else:
        log = open("log.txt","r")
        current_project = log.readline().strip()
        img_index = int(log.readline().strip())
        log.close()
        print("Loaded project!")
    print("poject name and index: " + current_project + " - " + str(img_index))
    img_file_prefix = current_project + "/image_"
    cv2.namedWindow("Zeitmaschine", cv2.WINDOW_NORMAL)

def capture_image():
    global img_index, last_picture_time, current_project, projects_folder
    ret, frame = cap.read()
    log = open("log.txt","w")
    log.write(current_project + "\n" + str(img_index))
    log.close()
    if ret:
        img_index += 1
        img_filename = f"{projects_folder}/{img_file_prefix}{img_index}.jpg"
        save_image_with_timestamp(frame, img_filename)
        last_picture_time = time.time()
    return frame

def save_image_with_timestamp(frame, filename):
    frame_with_timestamp = add_timestamp_to_image(frame)
    cv2.imwrite(filename, frame_with_timestamp)

def add_timestamp_to_image(frame):
    current_time = time.time()
    elapsed_time = int(current_time - program_start_time)
    hours, minutes, seconds = elapsed_time // 3600, (elapsed_time % 3600) // 60, elapsed_time % 60
    text = f"Elapsed Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    text_color = (255, 255, 255)
    text_bg_color = (0, 0, 0)
    (text_width, text_height) = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
    img = cv2.rectangle(frame, (0, 0), (text_width + 10, text_height + 10), text_bg_color, -1)
    org = (5, text_height + 5)
    img = cv2.putText(img, text, org, font, font_scale, text_color, font_thickness, cv2.LINE_AA)
    return img

def update_display():
    global img_shown_index, last_pressed_time, delta_time
    current_time = time.time()
    if current_time - last_pressed_time >= delta_time:
        img_shown_index = img_index
        display_image()
        last_pressed_time = current_time


def display_image():
    global playback_speed
    if playback_speed > 0:
        display_next_image()
    else:
        display_previous_image()         
    img_filename = f"projects/{img_file_prefix}{img_shown_index}.jpg"
    frame = cv2.imread(img_filename)
    if frame is not None:
        cv2.imshow("Zeitmaschine", frame)
        time.sleep(5.0 / playback_speed)  # Adjusts the delay based on playback speed


def display_previous_image():
    global img_shown_index
    img_shown_index -= 1
    if img_shown_index < 1:
        img_shown_index = img_index
    return 0

def display_next_image():
    global img_shown_index
    img_shown_index += 1
    if img_shown_index > img_index:
        img_shown_index = 0
    return 0

def handle_key_press():
    global img_shown_index, last_pressed_time, playback_speed
    key = cv2.waitKey(1)
    if key == ord('f'):
        state = "forward"
        playback_speed = 20
        print(state)
    elif key == ord('b'):
        state = "backward"
        playback_speed = 20
        print(state)
    elif key == ord('p'):
        state = "play/pause"
        playback_speed = 1
        print(state)
    elif key == ord('a'):
        display_previous_image()
        last_pressed_time = time.time()
    elif key == ord('s'):
        display_next_image()
        last_pressed_time = time.time()
    elif key == ord('q'):
        return False
    return True


def main_loop():
    global state
    while True:
        current_time = time.time()
        if current_time - last_picture_time >= delta_time:
            capture_image()
        update_display()
        if not handle_key_press():
            break

def cleanup():
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    initialize()
    main_loop()
    cleanup()