import time

class ProgramState:
    def __init__(self):
        # Image and Project State
        self.active_project = None
        self.selected_project = None
        self.img_capture_index = 0
        self.img_max_index = 0
        self.img_shown_index = 1
        
        # Time and Playback State
        self.program_start_time = time.time()
        self.playback_speed = 1
        self.playback_speed_index = 0
        self.image_step = 1
        self.last_keypress = time.time()
        
        # Flags and Paths
        self.default = True
        self.key = None
        self.projects = []
        self.projects_dict = {}
        self.base_url_active = ""
        self.base_url_display = ""
        self.img_file_prefix = "image_"