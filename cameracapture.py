import cv2

class CameraCapture:

    # Constants
    WIDTH = 1280 # width of the captured image
    HEIGHT = 970 # height of the captured image
    PIXELS_INSCRIPTION = 15 # number of pixels used on the upper left corner of the image to encode elapsed time


    def __init__(self, config):
        self.width = config["width"]
        self.height = config["height"]
        self.on_raspberry = config["on_raspberry"]
        self.cap = self.initialize()
   
    def initialize(self):
        """Attempts to initialize the camera."""
        # check current usb camera settings in terminal
        # v4l2-ctl -V 
        # check available usb camera settings in terminal
        # v4l2-ctl --list-formats-ext
        if self.on_raspberry:
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        return cap
    
    def image(self, elapsed_time, img_path):
        """Captures an image from the camera and saves it with a timestamp."""
        if not self.cap:
            print("Camera not initialized.")
            return
        ret, frame = self.cap.read()
        if ret:
            self.save_image_with_timestamp(elapsed_time, frame, img_path)

    def save_image_with_timestamp(self, elapsed_time, frame, img_path):
        """Saves the image with a timestamp overlay."""
        stats = self.map_time_255(elapsed_time)
        frame[0 : self.PIXELS_INSCRIPTION, 0 : self.PIXELS_INSCRIPTION] = (stats[0], stats[0], stats[0])
        frame[self.PIXELS_INSCRIPTION : 2*self.PIXELS_INSCRIPTION, 0 : self.PIXELS_INSCRIPTION] = (stats[1], stats[1], stats[1])
        frame[0 : self.PIXELS_INSCRIPTION, self.PIXELS_INSCRIPTION : 2*self.PIXELS_INSCRIPTION] = (stats[1], stats[1], stats[1])
        frame[2*self.PIXELS_INSCRIPTION : 3*self.PIXELS_INSCRIPTION, 0 : self.PIXELS_INSCRIPTION] = (stats[2], stats[2], stats[2])
        frame[0 : self.PIXELS_INSCRIPTION, 2*self.PIXELS_INSCRIPTION : 3*self.PIXELS_INSCRIPTION] = (stats[2], stats[2], stats[2])
        frame[3*self.PIXELS_INSCRIPTION : 4*self.PIXELS_INSCRIPTION, 0 : self.PIXELS_INSCRIPTION] = (stats[3], stats[3], stats[3])
        frame[0 : self.PIXELS_INSCRIPTION,3*self.PIXELS_INSCRIPTION : 4*self.PIXELS_INSCRIPTION] = (stats[3], stats[3], stats[3])
        cv2.imwrite(img_path, frame)

    def map_time_255(self, elapsed_time):
        days = elapsed_time // 86400
        hours = elapsed_time % 86400 // 3600
        minutes = elapsed_time % 3600 // 60
        seconds = elapsed_time % 60
        return [days* 10 + 4, hours * 10 + 4, minutes * 4 + 2 , seconds * 4 + 2]
    
    def map_255_time(self, stats):
        return [stats[0] // 10, stats[1] // 10, stats[2] // 4, stats[3] // 4] 
    
    def cleanup(self):
        if self.cap:
            self.cap.release()