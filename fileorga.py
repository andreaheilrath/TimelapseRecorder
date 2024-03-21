import os
import time

class FileOrga:
    DEFAULT_PROJECT = "default"  # Default project name

    def __init__(self, config, state):
        self.config = config
        self.state = state

        self.state['img_capture_index'] = 0
        self.ensure_directory_exists(self.config["projects_folder"])
        # Additional initialization as needed

    def setup_project(self, state):
        """Sets up the project directory and reads the last state from the log file."""
        self.ensure_directory_exists(self.config["projects_folder"])
        self.get_projects()
        self.select_project()
        self.state['selected_project'] = self.state['active_project']
        self.state['selected_project_index'] = self.state['projects'].index(self.state['selected_project'])
        
        self.state['base_url_active'] = os.path.join(self.config["projects_folder"], self.state["active_project"], self.state['img_file_prefix'])
        self.state['base_url_display'] = self.state['base_url_active']
        
        print(f"Project: {self.state['active_project']} | Current Image Index: {self.state['img_capture_index']}")

    def get_projects(self):
        """Returns a list of projects sorted by creation time."""
        projects_list = [d for d in os.listdir(self.config["projects_folder"]) if os.path.isdir(os.path.join(self.config["projects_folder"], d))]
        projects_list.sort(key=lambda d: -os.path.getctime(os.path.join(self.config["projects_folder"], d)))
        if not projects_list:
            projects_list.append(self.DEFAULT_PROJECT)
            self.ensure_directory_exists(os.path.join(self.config["projects_folder"], self.DEFAULT_PROJECT))
        for project in projects_list:
            dir_path = os.path.join(self.config["projects_folder"], project)
            number_of_files = len([entry for entry in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, entry))])
            self.state['projects_dict'][project] = number_of_files
        self.state['projects'] = projects_list
        print("Projects Dict:", self.state['projects_dict'])

    def select_project(self):
        """Selects the current project from the available projects."""
        for project in self.state['projects']:
            if self.is_directory_empty(os.path.join(self.config["projects_folder"], project)):
                self.state['active_project'] = project
                self.state['program_start_time'] = time.time()
                self.state['img_capture_index'] = 0
                return
        if self.state['active_project'] in self.state['projects']:
            return
        self.state['active_project'] = self.DEFAULT_PROJECT
        

    def ensure_directory_exists(self, path):
        """Ensures that a directory exists at the given path."""
        os.makedirs(path, exist_ok=True)

    def is_directory_empty(self, path):
        """Checks if a directory is empty."""
        return next(os.scandir(path), None) is None