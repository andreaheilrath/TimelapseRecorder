import os
import time

class FileOrga:

    PROJECTS_FOLDER = "projects"  # Folder where project images are stored
    DEFAULT_PROJECT = "default"  # Default project name

    def __init__(self, projects_folder, default_project="default"):
        self.projects_folder = projects_folder
        self.active_project = default_project
        self.img_capture_index = 0
        self.ensure_directory_exists(self.projects_folder)
        self.projects = []
        self.projects_dict = {}
        # Additional initialization as needed

    def setup_project(self, state):
        """Sets up the project directory and reads the last state from the log file."""
        self.ensure_directory_exists(self.PROJECTS_FOLDER)
        self.get_projects()
        self.select_project()
        self.selected_project = self.active_project
        self.selected_project_index = self.projects.index(self.selected_project)
        print(f"Project: {self.active_project} | Current Image Index: {self.img_capture_index}")
        print(self.selected_project_index)

    def get_projects(self):
        """Returns a list of projects sorted by creation time."""
        projects_list = [d for d in os.listdir(self.PROJECTS_FOLDER) if os.path.isdir(os.path.join(self.PROJECTS_FOLDER, d))]
        projects_list.sort(key=lambda d: -os.path.getctime(os.path.join(self.PROJECTS_FOLDER, d)))
        if not projects_list:
            projects_list.append(self.DEFAULT_PROJECT)
            self.ensure_directory_exists(os.path.join(self.PROJECTS_FOLDER, self.DEFAULT_PROJECT))
        for project in projects_list:
            dir_path = os.path.join(self.PROJECTS_FOLDER, project)
            number_of_files = len([entry for entry in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, entry))])
            self.projects_dict[project] = number_of_files
        self.projects = projects_list
        print("Projects Dict:", self.projects_dict)

    def select_project(self):
        """Selects the current project from the available projects."""
        for project in self.projects:
            if self.is_directory_empty(os.path.join(self.PROJECTS_FOLDER, project)):
                self.active_project = project
                self.program_start_time = time.time()
                self.img_capture_index = 0
                return
        if self.active_project in self.projects:
            return
        self.active_project = self.DEFAULT_PROJECT
        

    def ensure_directory_exists(self, path):
        """Ensures that a directory exists at the given path."""
        os.makedirs(path, exist_ok=True)

    def is_directory_empty(self, path):
        """Checks if a directory is empty."""
        return next(os.scandir(path), None) is None