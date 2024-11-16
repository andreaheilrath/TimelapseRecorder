import cv2

class CameraCapture:

    # Constants
    WIDTH = 1280 # width of the captured image
    HEIGHT = 970 # height of the captured image
    PIXELS_INSCRIPTION = 15 # number of pixels used on the upper left corner of the image to encode elapsed time


    def __init__(self, config, state):
        self.width = config["width"]
        self.height = config["height"]
        self.on_raspberry = config["on_raspberry"]
        self.cap = self.initialize()
        self.config = config
        self.state = state
   
    def initialize(self, device_number = 0):
        """Attempts to initialize the camera."""
        # check current usb camera settings in terminal
        # v4l2-ctl -V 
        # check available usb camera settings in terminal
        # v4l2-ctl --list-formats-ext
        if self.on_raspberry:
            cap = cv2.VideoCapture(device_number, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(device_number)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        return cap
    
    def image(self, elapsed_time):
        """Captures an image from the camera and saves it with a timestamp."""
        if not self.cap:
            print("Camera not initialized.")
            return
        ret, frame = self.cap.read()
        if ret:
            img_path = self.state['base_url_active'] + str(self.state["img_capture_index"]) + ".jpg"   
            self.save_image_with_timestamp(frame, img_path, elapsed_time)

    def save_image_with_timestamp(self, frame, img_path, elapsed_time):
        """Saves the image with a timestamp overlay."""
        stats = self.map_time_255(elapsed_time)
        pix_range = self.config["pixels_for_timestamp"]
        frame[0 : pix_range, 0 : pix_range] =               stats[0] #(stats[0], stats[0], stats[0])
        frame[pix_range : 2*pix_range, 0 : pix_range] =     (stats[1], stats[1], stats[1])
        frame[0 : pix_range, pix_range : 2*pix_range] =     (stats[1], stats[1], stats[1])
        frame[2*pix_range : 3*pix_range, 0 : pix_range] =   (stats[2], stats[2], stats[2])
        frame[0 : pix_range, 2*pix_range : 3*pix_range] =   (stats[2], stats[2], stats[2])
        frame[3*pix_range : 4*pix_range, 0 : pix_range] =   (stats[3], stats[3], stats[3])
        frame[0 : pix_range,3*pix_range : 4*pix_range] =    (stats[3], stats[3], stats[3])
        
        cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

    def map_time_255(self, elapsed_time):
        days = elapsed_time // 86400
        hours = elapsed_time % 86400 // 3600
        minutes = elapsed_time % 3600 // 60
        seconds = elapsed_time % 60
        return [days* 10 + 4, hours * 10 + 4, minutes * 4 + 2 , seconds * 4 + 2]
      
    def cleanup(self):
        if self.cap:
            self.cap.release()
