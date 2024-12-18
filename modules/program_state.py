import time

class ProgramState:
    def __init__(self):

        # Flags and Paths
        self.default = True
        self.img_file_prefix = "image_"

        self.projects = []
        self.projects_dict = {}

        # Image and Project State
        self.projectName_record = None
        self.baseUrl_record = ""
        self.imgIndex_record = 0
        self.imgIndices_record = []
        self.imgMaxIndex_record = 0

        self.projectName_display = None
        self.projectName_display_index = 0
        self.baseUrl_display = ""
        self.imgIndex_display = 1
        self.imgIndices_display = []
        self.imgMaxIndex_display = 0

        
        # Time and Playback State
        self.program_start_time = time.time()
        self.key = None
        self.last_keypress = time.time()

        self.playback_speed = 1
        self.playback_speed_index = 0
        self.image_step = 1


        
