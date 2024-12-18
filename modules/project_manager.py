import os
import time

class ProjectManager:
    """Manages project directories and state initialization."""
    DEFAULT_PROJECT = "default"  # Default project name

    def __init__(self, config, state):
        """Initializes the ProjectManager with configuration and state."""
        self.config = config
        self.state = state
        self.ensure_directory_exists(self.config["projects_folder"])

    def setup_project(self):
        """Sets up the active project and initializes paths."""
        self.ensure_directory_exists(self.config["projects_folder"])
        self.get_projects()
        self.select_project()
        
        self.state.selected_project = self.state.active_project
        self.state.selected_project_index = self.state.projects.index(self.state.selected_project)

        # Define active and display URLs for image storage
        self.state.base_url_active = os.path.join(
            self.config["projects_folder"], 
            self.state.active_project, 
            self.state.img_file_prefix
        )
        self.state.base_url_display = self.state.base_url_active

        print(f"Project: {self.state.active_project} | Current Image Index: {self.state.img_capture_index}")

    def get_projects(self):
        """Retrieves projects and sorts them by creation time."""
        projects_folder = self.config["projects_folder"]
        projects_list = [
            d for d in os.listdir(projects_folder) 
            if os.path.isdir(os.path.join(projects_folder, d))
        ]

        # Sort by creation time (newest first)
        projects_list.sort(key=lambda d: -os.path.getctime(os.path.join(projects_folder, d)))
        
        # If no projects exist, create the default project
        if not projects_list:
            projects_list.append(self.DEFAULT_PROJECT)
            self.ensure_directory_exists(os.path.join(projects_folder, self.DEFAULT_PROJECT))

        # Count files in each project directory
        for project in projects_list:
            dir_path = os.path.join(projects_folder, project)
            file_count = len([
                entry for entry in os.listdir(dir_path) 
                if os.path.isfile(os.path.join(dir_path, entry))
            ])
            self.state.projects_dict[project] = file_count

        self.state.projects = projects_list
        print("Projects Dict:", self.state.projects_dict)

    def select_project(self):
        """Selects the project to use, prioritizing empty directories."""
        projects_folder = self.config["projects_folder"]
        for project in self.state.projects:
            project_path = os.path.join(projects_folder, project)
            if self.is_directory_empty(project_path):
                self.state.active_project = project
                self.state.program_start_time = time.time()
                self.state.img_capture_index = 0
                return

        # If no empty project directories, use default or existing active project
        if self.state.active_project in self.state.projects:
            return

        self.state.active_project = self.DEFAULT_PROJECT

    def ensure_directory_exists(self, path):
        """Ensures that a directory exists at the specified path."""
        os.makedirs(path, exist_ok=True)

    def is_directory_empty(self, path):
        """Checks if the given directory is empty."""
        return next(os.scandir(path), None) is None