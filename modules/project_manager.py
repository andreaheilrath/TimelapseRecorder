import os
import time
from typing import Any


class ProjectManager:
    """Manages project directories and state initialization."""
    DEFAULT_PROJECT = "default"  # Default project name
    JPG_EXTENSION = ".jpg"

    def __init__(self, config: dict[str, Any], state: Any) -> None:
        """Initializes the ProjectManager with configuration and state."""
        self.config = config
        self.state = state
        self.default_project = self.config.get("default_project", self.DEFAULT_PROJECT)
        self.ensure_directory_exists(self.config["projects_folder"])

    def ensure_directory_exists(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def project_image_base_path(self, project_name: str) -> str:
        return os.path.join(self.config["projects_folder"], project_name, self.state.img_file_prefix)

    def setup(self) -> None:
        self.get_projects()

        if self.config["capture"]:
            self.setup_recording_project()
  
        self.setup_display_project()

###################################################################################################
    def get_projects(self) -> None:
        """Retrieves projects and sorts them by creation time."""
        projects_list = [
            d for d in os.listdir(self.config["projects_folder"])
            if os.path.isdir(os.path.join(self.config["projects_folder"], d))
        ]

        if self.default_project not in projects_list:
            self.ensure_directory_exists(os.path.join(self.config["projects_folder"], self.default_project))
            projects_list.append(self.default_project)

        # Sort by creation time (newest first)
        projects_list.sort(key=lambda d: -os.path.getctime(os.path.join(self.config["projects_folder"], d)))

        self.state.projects_dict = {}

        # Count files in each project directory
        for project in projects_list:
            dir_path = os.path.join(self.config["projects_folder"], project)

            file_entries = [
                entry for entry in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, entry)) and entry.startswith(self.state.img_file_prefix)
            ]

            # Extract numeric indices from file names
            indices = []
            for entry in file_entries:
                number = entry.replace(self.state.img_file_prefix, "").replace(self.JPG_EXTENSION, "")
                if number.isdigit():
                    indices.append(int(number))

            indices.sort()  # Ensure indices are sorted

            self.state.projects_dict[project] = {
                "indices": indices,
                "max_index": len(indices)
            }

        self.state.projects = projects_list
        print("self.state.projects:", projects_list)

###################################################################################################
    def setup_recording_project(self) -> None:

        #Checks if one of the given directories is empty.
        for project in self.state.projects:
            if not self.state.projects_dict[project]["indices"]: #check if one of project folders is empty
                self.state.project_name_record = project
                self.state.program_start_time = time.time()
                self.state.img_indices_record = self.state.projects_dict[project]["indices"]
                self.state.img_max_index_record = self.state.projects_dict[project]["max_index"]
                self.state.img_index_record = 0

                # Define recording and display URLs for image storage
                self.state.base_url_record = self.project_image_base_path(self.state.project_name_record)
                return

        # If no empty project directories, use default or existing recording project
        if self.state.project_name_record in self.state.projects:
            self.state.img_indices_record = self.state.projects_dict[self.state.project_name_record]["indices"]
            self.state.img_max_index_record = self.state.projects_dict[self.state.project_name_record]["max_index"]
            self.state.img_index_record = max(self.state.img_index_record, len(self.state.img_indices_record))

            # Define recording and display URLs for image storage
            self.state.base_url_record = self.project_image_base_path(self.state.project_name_record)
            return

        self.state.project_name_record = self.default_project
        if self.state.project_name_record not in self.state.projects_dict:
            self.ensure_directory_exists(os.path.join(self.config["projects_folder"], self.state.project_name_record))
            self.state.projects.append(self.state.project_name_record)
            self.state.projects_dict[self.state.project_name_record] = {"indices": [], "max_index": 0}

        self.state.img_indices_record = self.state.projects_dict[self.state.project_name_record]["indices"]
        self.state.img_max_index_record = self.state.projects_dict[self.state.project_name_record]["max_index"]
        self.state.img_index_record = max(self.state.img_index_record, len(self.state.img_indices_record))

        self.state.base_url_record = self.project_image_base_path(self.state.project_name_record)
        print(f"Recording Project: {self.state.project_name_record} | Current Image Index: {self.state.img_index_record}")


###################################################################################################
    def setup_display_project(self) -> None:

        if self.config["capture"]:
            self.state.project_name_display = self.state.project_name_record
            self.state.project_name_display_index = self.state.projects.index(self.state.project_name_record)
            self.state.base_url_display = self.state.base_url_record
            self.state.img_indices_display = self.state.img_indices_record
            self.state.img_max_index_display = len(self.state.img_indices_display)
            self.state.img_index_display = -1
        elif self.config["default_display"] in self.state.projects:
            self.state.project_name_display = self.config["default_display"]
            self.state.project_name_display_index = self.state.projects.index(self.state.project_name_display)
            self.state.base_url_display = self.project_image_base_path(self.state.project_name_display)
            self.state.img_indices_display = self.state.projects_dict[self.state.project_name_display]["indices"]
            self.state.img_max_index_display = len(self.state.img_indices_display)
            self.state.img_index_display = -1
        else:
            self.state.project_name_display_index = 0
            self.state.project_name_display = self.state.projects[self.state.project_name_display_index]
            self.state.base_url_display = self.project_image_base_path(self.state.project_name_display)
            self.state.img_indices_display = self.state.projects_dict[self.state.project_name_display]["indices"]
            self.state.img_max_index_display = len(self.state.img_indices_display)
            self.state.img_index_display = -1

        print("base url display", self.state.base_url_display)
        print(f"Display Project: {self.state.project_name_display} | Current Image Index: {self.state.img_index_record}")
