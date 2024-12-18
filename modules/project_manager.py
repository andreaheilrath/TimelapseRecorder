import os
import time

class ProjectManager:
    """Manages project directories and state initialization."""
    DEFAULT_PROJECT = "default"  # Default project name

    def __init__(self, config, state):
        """Initializes the ProjectManager with configuration and state."""
        self.config = config
        self.state = state
        os.makedirs(self.config["projects_folder"], exist_ok=True) # ensure that project directory exists

    def setup(self):
        self.get_projects()

        if self.config["capture"]:
            self.setup_recording_project()
  
        self.setup_display_project()

###################################################################################################
    def get_projects(self):
        """Retrieves projects and sorts them by creation time."""
        projects_list = [
            d for d in os.listdir(self.config["projects_folder"]) 
            if os.path.isdir(os.path.join(self.config["projects_folder"], d))
        ]

        # Sort by creation time (newest first)
        projects_list.sort(key=lambda d: -os.path.getctime(os.path.join(self.config["projects_folder"], d)))
        
        # If no projects exist, create the default project
        if not projects_list:
            projects_list.append(self.DEFAULT_PROJECT)
            self.ensure_directory_exists(os.path.join(self.config["projects_folder"], self.DEFAULT_PROJECT))

        # Count files in each project directory
        for project in projects_list:
            dir_path = os.path.join(self.config["projects_folder"], project)

            file_entries = [
                entry for entry in os.listdir(dir_path) 
                if os.path.isfile(os.path.join(dir_path, entry)) and entry.startswith(self.state.img_file_prefix)
            ]
            
            # Extract numeric indices from file names
            indices = [
                int(entry.replace(self.state.img_file_prefix, "").replace(".jpg", ""))
                for entry in file_entries
            ]

            indices.sort()  # Ensure indices are sorted
            
            self.state.projects_dict[project] = {
                "indices": indices,
                "max_index" : len(indices)-1
            }

        self.state.projects = projects_list
        print("self.state.projects:", projects_list)

###################################################################################################
    def setup_recording_project(self):

        #Checks if one of the given directories is empty.
        for project in self.state.projects: 
            if not self.state.projects_dict[project]["indices"]: #check if one of project folders is empty
                self.state.projectName_record = project
                self.state.program_start_time = time.time()
                self.state.imgIndices_record = self.state.projects_dict[project]["indices"]
                self.state.img_max_indices = self.state.projects_dict[project]["max_index"]
                self.state.imgIndex_record = 0

                # Define recording and display URLs for image storage
                self.state.baseUrl_record = os.path.join(
                    self.config["projects_folder"], 
                    self.state.projectName_record, 
                    self.state.img_file_prefix
                )
                return

        # If no empty project directories, use default or existing recording project
        if self.state.projectName_record in self.state.projects:
            self.state.projectName_display = self.state.projectName_record
            self.state.imgIndices_record = self.state.projects_dict[self.state.projectName_record]["indices"]
            self.state.imgMaxIndex_display = self.state.projects_dict[self.state.projectName_record]["max_index"]

            # Define recording and display URLs for image storage
            self.state.baseUrl_record = os.path.join(
                self.config["projects_folder"], 
                self.state.projectName_record, 
                self.state.img_file_prefix
            )
            return
        
        # Define recording and display URLs for image storage
        self.state.baseUrl_record = os.path.join(
            self.config["projects_folder"], 
            self.state.projectName_record, 
            self.state.img_file_prefix
        )
        print(f"Recording Project: {self.state.projectName_record} | Current Image Index: {self.state.imgIndex_record}")


###################################################################################################
    def setup_display_project(self):
        
        if self.config["capture"]:
            self.state.projectName_display = self.state.projectName_record
            self.state.projectName_display_index = self.state.projects.index(self.state.projectName_record)
            self.state.baseUrl_display = self.state.baseUrl_record
            self.state.imgIndices_display = self.state.imgIndices_record
        elif self.config["default_display"] in self.state.projects:
            self.state.projectName_display = self.config["default_display"]
            self.state.projectName_display_index = self.state.projects.index(self.state.projectName_record)
            self.state.baseUrl_display = os.path.join(
                self.config["projects_folder"], 
                self.state.projectName_display, 
                self.state.img_file_prefix
            )
            self.state.imgIndices_display = self.state.projects_dict[self.state.projectName_display]["indices"]
            self.state.imgMaxIndex_display = self.state.projects_dict[self.state.projectName_display]["max_index"]
            self.state.imgIndex_display = 0
        else:
            self.state.projectName_display_index = 0
            self.state.projectName_display = self.state.projects[self.state.projectName_display_index]
            self.state.baseUrl_display = os.path.join(
                self.config["projects_folder"], 
                self.state.projectName_display, 
                self.state.img_file_prefix
            )
            self.state.imgIndices_display = self.state.projects_dict[self.state.projectName_display]["indices"]
            self.state.imgMaxIndex_display = self.state.projects_dict[self.state.projectName_display]["max_index"]
            self.state.imgIndex_display = 0
        
        print("base url display", self.state.baseUrl_display)
        print(f"Display Project: {self.state.projectName_display} | Current Image Index: {self.state.imgIndex_record}")


