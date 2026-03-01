import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProgramState:
    is_default_mode: bool = True
    img_file_prefix: str = "image_"

    projects: list[str] = field(default_factory=list)
    projects_dict: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Image and project state
    project_name_record: str | None = None
    base_url_record: str = ""
    img_index_record: int = 0
    img_indices_record: list[int] = field(default_factory=list)

    project_name_display: str | None = None
    project_name_display_index: int = 0
    base_url_display: str = ""
    img_index_display: int = -1
    img_indices_display: list[int] = field(default_factory=list)

    # Time and playback state
    program_start_time: float = field(default_factory=time.time)
    key: int | None = None
    last_keypress: float = field(default_factory=time.time)

    playback_speed: int = 1
    is_paused: bool = False
    display_frame_delta_seconds: float = 1.0
    frame_advance_accumulator: float = 0.0
