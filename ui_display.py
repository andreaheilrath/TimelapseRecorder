import cv2
import time
import numpy as np

class UIDisplay:
    DEFAULT_PLAYBACK_SPEED = 1  # Default playback speed when reviewing images
    PLAYBACK_SPEEDS = [16, 32, 64, 128, 256, 512, 1028]  # Playback speeds for reviewing images
    FULLSCREEN = False # set True for performance mode
    WINDOW_NAME = "Zeitmaschine"  # Window name for the display

    def __init__(self, config, state):
        self.window_name = "Time Lapse"
        self.state = state
        self.config = config
        cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
        if config["fullscreen"]:
            cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        self.playback_speed = self.DEFAULT_PLAYBACK_SPEED
        self.playback_speed_index = 0    

    def play_movie(self):
        """Plays the captured images as a time-lapse movie."""
        if self.state['img_max_index']:
            self.state['img_shown_index'] = (self.state['img_shown_index'] + (1 if self.state['playback_speed'] > 0 else -1)) % self.state['img_max_index']
        else:
            self.state['img_shown_index']  = 0
        self.update_display(self.state['img_shown_index'] )
        print(self.config['capture_interval'], self.state['playback_speed'])
        self.key = cv2.waitKey(int(1000 * self.config['capture_interval'] / abs(self.state['playback_speed'])))

    def return_to_default(self):
        delta = (time.time() - self.state['last_keypress'])
        if delta > 120:
            self.selected_project = self.active_project
            self.state['playback_speed'] = self.config['playback_speeds'][4]
            self.default = True
            print("Returning to Default")

    def update_display(self, index):
            """Updates the display with the image at the given index."""

            img_filename = self.state['base_file_name'] + f"{index}.jpg"
            frame = cv2.imread(img_filename)

            if frame is not None:
                font = cv2.FONT_HERSHEY_DUPLEX #cv2.FONT_HERSHEY_SIMPLEX #

                height = 40
                font_size = 1.2
                font_weight = 1
                font_color = (255, 255, 255)

                if self.LANDSCAPE:
                    UI_element = np.zeros((60,self.WIDTH-self.PIXELS_INSCRIPTION,3), np.uint8)

                    # draw black background for text
                    cv2.rectangle(UI_element, (0, 0), (self.WIDTH-self.PIXELS_INSCRIPTION, 59), (0, 0, 0), -1)
                    
                    # print elapsed time on canvas
                    space = 120
                    left_space = 30
                    value_days = int(frame[self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    value_hours = int(frame[self.PIXELS_INSCRIPTION + self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    value_minutes = int(frame[2*self.PIXELS_INSCRIPTION + self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    value_seconds = int(frame[3*self.PIXELS_INSCRIPTION + self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    elapsed_time = self.map_255_time([value_days, value_hours, value_minutes, value_seconds])
                    cv2.putText(UI_element, str(elapsed_time[0]), (left_space, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, str(elapsed_time[1]), (left_space + space , height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, str(elapsed_time[2]), (left_space + 2*space , height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, str(elapsed_time[3]), (left_space + 3*space, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 'd', (left_space + space//2, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 'h', (left_space + space + space//2, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 'm', (left_space + 2*space + space//2, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 's', (left_space + 3*space + space//2, height), font, font_size, font_color, font_weight)
                    
                    # print project on canvas
                    cv2.putText(UI_element, str(self.selected_project), (6*self.WIDTH//8, height), font, font_size, font_color, font_weight)
                    
                    # print playback speed on canvas
                    if self.playback_speed == 1:
                        icon = "> "
                    elif self.playback_speed > 1:
                        icon = ">>"
                    elif self.playback_speed < 1:
                        icon = "<<"
                    cv2.putText(UI_element, icon + str(abs(self.playback_speed)) + "x", (4*self.WIDTH//10, height), font, font_size, font_color, font_weight)      
                    frame[0:60, self.PIXELS_INSCRIPTION:self.WIDTH] = UI_element
                
                else:
                    UI_element = np.zeros((60,self.HEIGHT-self.PIXELS_INSCRIPTION,3), np.uint8)

                    # draw black background for text
                    cv2.rectangle(UI_element, (0, 0), (self.HEIGHT-self.PIXELS_INSCRIPTION, 59), (0, 0, 0), -1)
                    
                    # print elapsed time on canvas
                    space = 100
                    left_space = 680
                    value_days = int(frame[self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    value_hours = int(frame[self.PIXELS_INSCRIPTION + self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    value_minutes = int(frame[2*self.PIXELS_INSCRIPTION + self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    value_seconds = int(frame[3*self.PIXELS_INSCRIPTION + self.PIXELS_INSCRIPTION //2, self.PIXELS_INSCRIPTION//2].mean())
                    elapsed_time = self.map_255_time([value_days, value_hours, value_minutes, value_seconds])
                    cv2.putText(UI_element, str(elapsed_time[0]), (left_space, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, str(elapsed_time[1]), (left_space + space , height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, str(elapsed_time[2]), (left_space + 2*space , height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, str(elapsed_time[3]), (left_space + 3*space, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 'd', (left_space + space//2, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 'h', (left_space + space + space//2, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 'm', (left_space + 2*space + space//2, height), font, font_size, font_color, font_weight)
                    cv2.putText(UI_element, 's', (left_space + 3*space + space//2, height), font, font_size, font_color, font_weight)
                    
                    # print project on canvas
                    cv2.putText(UI_element, str(self.selected_project), (20, height), font, font_size, font_color, font_weight)
                    
                    # print playback speed on canvas
                    if self.playback_speed == 1:
                        icon = "> "
                    elif self.playback_speed > 1:
                        icon = ">>"
                    elif self.playback_speed < 1:
                        icon = "<<"
                    cv2.putText(UI_element, icon + str(abs(self.playback_speed)) + "x", (4*self.HEIGHT//10, height), font, font_size, font_color, font_weight)      
                    
                    UI_element = cv2.rotate(UI_element, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    frame[self.PIXELS_INSCRIPTION:self.HEIGHT, 0:60] = UI_element

                cv2.imshow(self.WINDOW_NAME, frame)
  

    def cleanup(self):
        cv2.destroyAllWindows()