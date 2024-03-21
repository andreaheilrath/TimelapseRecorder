import cv2
import time
import numpy as np

class UIDisplay:
    DEFAULT_PLAYBACK_SPEED = 1  # Default playback speed when reviewing images
    PLAYBACK_SPEEDS = [16, 32, 64, 128, 256, 512, 1028]  # Playback speeds for reviewing images
    FULLSCREEN = False # set True for performance mode

    def __init__(self, config, state):
        self.window_name = "Time Lapse"
        self.state = state
        self.config = config
        cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)
        if config["fullscreen"]:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        self.state['playback_speed']  = self.DEFAULT_PLAYBACK_SPEED 

    def play_movie(self):
        """Plays the captured images as a time-lapse movie."""
        if self.state['img_max_index']:
            self.state['img_shown_index'] = (self.state['img_shown_index'] + (1 if self.state['playback_speed'] > 0 else -1)) % self.state['img_max_index']
        else:
            self.state['img_shown_index']  = 0
        self.update_display(self.state['img_shown_index'] )
        self.state['key'] = cv2.waitKey(int(1000 * self.config['capture_interval'] / abs(self.state['playback_speed'])))

    def return_to_default(self):
        delta = (time.time() - self.state['last_keypress'])
        if delta > 120:
            self.state['selected_project'] = self.state['active_project']
            self.state['playback_speed'] = self.config['playback_speeds'][4]
            self.state['default'] = True
            print("Returning to Default")

    def update_display(self, index):
            """Updates the display with the image at the given index."""
            img_filename = self.state['base_url_display'] + f"{index}.jpg"
            frame = cv2.imread(img_filename)

            font_specs = {
                'fontFace' : cv2.FONT_HERSHEY_DUPLEX, #cv2.FONT_HERSHEY_SIMPLEX #
                'fontScale' : 1.2,
                'color' : (255, 255, 255),
                'thickness' : 1
            }

            if frame is not None:
                
                height = 40

                if self.config['landscape']:
                    UI_element = np.zeros((60,self.config['width']-self.config['pixels_for_timestamp'],3), np.uint8)

                    # draw black background for text
                    cv2.rectangle(UI_element, (0, 0), (self.config['width']-self.config['pixels_for_timestamp'], 59), (0, 0, 0), -1)
                    
                    # print elapsed time on canvas
                    space = 120
                    left_space = 30
                    value_days = int(frame[self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    value_hours = int(frame[self.config['pixels_for_timestamp'] + self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    value_minutes = int(frame[2*self.config['pixels_for_timestamp'] + self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    value_seconds = int(frame[3*self.config['pixels_for_timestamp'] + self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    elapsed_time = self.map_255_time([value_days, value_hours, value_minutes, value_seconds])
                    cv2.putText(UI_element, str(elapsed_time[0]), (left_space, height), **font_specs)
                    cv2.putText(UI_element, str(elapsed_time[1]), (left_space + space , height), **font_specs)
                    cv2.putText(UI_element, str(elapsed_time[2]), (left_space + 2*space , height), **font_specs)
                    cv2.putText(UI_element, str(elapsed_time[3]), (left_space + 3*space, height), **font_specs)
                    cv2.putText(UI_element, 'd', (left_space + space//2, height), **font_specs)
                    cv2.putText(UI_element, 'h', (left_space + space + space//2, height), **font_specs)
                    cv2.putText(UI_element, 'm', (left_space + 2*space + space//2, height), **font_specs)
                    cv2.putText(UI_element, 's', (left_space + 3*space + space//2, height),**font_specs)
                    
                    # print project on canvas
                    cv2.putText(UI_element, str(self.state['selected_project']), (6*self.config['width']//8, height), **font_specs)
                    
                    # print playback speed on canvas
                    if self.state['playback_speed']  == 1:
                        icon = "> "
                    elif self.state['playback_speed']  > 1:
                        icon = ">>"
                    elif self.state['playback_speed']  < 1:
                        icon = "<<"
                    cv2.putText(UI_element, icon + str(abs(self.state['playback_speed'] )) + "x", (4*self.config['width']//10, height), **font_specs)      
                    frame[0:60, self.config['pixels_for_timestamp']:self.config['width']] = UI_element
                
                else:
                    UI_element = np.zeros((60,self.config['height']-self.config['pixels_for_timestamp'],3), np.uint8)

                    # draw black background for text
                    cv2.rectangle(UI_element, (0, 0), (self.config['height']-self.config['pixels_for_timestamp'], 59), (0, 0, 0), -1)
                    
                    # print elapsed time on canvas
                    space = 100
                    left_space = 680
                    value_days = int(frame[self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    value_hours = int(frame[self.config['pixels_for_timestamp'] + self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    value_minutes = int(frame[2*self.config['pixels_for_timestamp'] + self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    value_seconds = int(frame[3*self.config['pixels_for_timestamp'] + self.config['pixels_for_timestamp'] //2, self.config['pixels_for_timestamp']//2].mean())
                    elapsed_time = self.map_255_time([value_days, value_hours, value_minutes, value_seconds])
                    cv2.putText(UI_element, str(elapsed_time[0]), (left_space, height), **font_specs)
                    cv2.putText(UI_element, str(elapsed_time[1]), (left_space + space , height), **font_specs)
                    cv2.putText(UI_element, str(elapsed_time[2]), (left_space + 2*space , height), **font_specs)
                    cv2.putText(UI_element, str(elapsed_time[3]), (left_space + 3*space, height), **font_specs)
                    cv2.putText(UI_element, 'd', (left_space + space//2, height), **font_specs)
                    cv2.putText(UI_element, 'h', (left_space + space + space//2, height), **font_specs)
                    cv2.putText(UI_element, 'm', (left_space + 2*space + space//2, height), **font_specs)
                    cv2.putText(UI_element, 's', (left_space + 3*space + space//2, height), **font_specs)
                    
                    # print project on canvas
                    cv2.putText(UI_element, str(self.state['selected_project']), (20, height), **font_specs)
                    
                    # print playback speed on canvas
                    if self.state['playback_speed']  == 1:
                        icon = "> "
                    elif self.state['playback_speed']  > 1:
                        icon = ">>"
                    elif self.state['playback_speed']  < 1:
                        icon = "<<"
                    cv2.putText(UI_element, icon + str(abs(self.state['playback_speed'] )) + "x", (4*self.config['height']//10, height), **font_specs)      
                    
                    UI_element = cv2.rotate(UI_element, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    frame[self.config['pixels_for_timestamp']:self.config['height'], 0:60] = UI_element

                cv2.imshow(self.window_name, frame)
  
    def map_255_time(self, stats):
        return [stats[0] // 10, stats[1] // 10, stats[2] // 4, stats[3] // 4] 
    
    def cleanup(self):
        cv2.destroyAllWindows()