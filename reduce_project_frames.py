#!/usr/bin/env python3
"""Reduce frame count in a project and reindex image files.

Example:
    python3 reduce_project_frames.py default --delete-fraction 1/2
    python3 reduce_project_frames.py default --delete-fraction 2/3 --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import uuid
from pathlib import Path


JPG_EXT = ".jpg"
INDEX_RE_TEMPLATE = r"^{prefix}(?P<index>\d+)\.jpg$"


def parse_fraction(value: str) -> tuple[int, int]:
    try:
        numerator_str, denominator_str = value.split("/", maxsplit=1)
        numerator = int(numerator_str)
        denominator = int(denominator_str)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Fraction must have the form A/B, e.g. 1/2") from exc

    if denominator <= 0:
        raise argparse.ArgumentTypeError("Denominator must be > 0")
    if numerator < 0:
        raise argparse.ArgumentTypeError("Numerator must be >= 0")
    if numerator >= denominator:
        raise argparse.ArgumentTypeError("Numerator must be smaller than denominator")
    return numerator, denominator


def collect_project_images(project_dir: Path, prefix: str) -> list[Path]:
    index_re = re.compile(INDEX_RE_TEMPLATE.format(prefix=re.escape(prefix)))
    indexed_files: list[tuple[int, Path]] = []

    for entry in project_dir.iterdir():
        if not entry.is_file():
            continue
        match = index_re.match(entry.name)
        if not match:
            continue
        indexed_files.append((int(match.group("index")), entry))

    indexed_files.sort(key=lambda item: item[0])
    return [path for _, path in indexed_files]


def should_keep(frame_position: int, delete_num: int, delete_den: int) -> bool:
    keep_per_block = delete_den - delete_num
    return (frame_position % delete_den) < keep_per_block


def reduce_project_frames(
    project_dir: Path,
    prefix: str,
    delete_num: int,
    delete_den: int,
    dry_run: bool,
    yes: bool,
) -> None:
    files = collect_project_images(project_dir, prefix)
    total = len(files)

    if total == 0:
        print(f"No files found in '{project_dir}' matching '{prefix}<index>.jpg'.")
        return

    keep_files: list[Path] = []
    delete_files: list[Path] = []
    for position, file_path in enumerate(files):
        if should_keep(position, delete_num, delete_den):
            keep_files.append(file_path)
        else:
            delete_files.append(file_path)

    if not keep_files:
        raise RuntimeError(
            "Reduction would delete all files. Choose a smaller delete fraction."
        )

    print(f"Project: {project_dir}")
    print(f"Total frames: {total}")
    print(f"Delete fraction: {delete_num}/{delete_den}")
    print(f"Keep frames: {len(keep_files)}")
    print(f"Delete frames: {len(delete_files)}")

    if dry_run:
        print("Dry-run enabled. No files were changed.")
        return

    if not yes:
        answer = input("Are you sure you want to delete and reindex files? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Aborted. No files were changed.")
            return

    for file_path in delete_files:
        file_path.unlink()

    tmp_token = uuid.uuid4().hex
    tmp_paths: list[Path] = []

    # Stage 1: rename kept files to temporary unique names.
    for new_index, old_path in enumerate(keep_files):
        tmp_name = f".tmp_reindex_{tmp_token}_{new_index}{JPG_EXT}"
        tmp_path = old_path.with_name(tmp_name)
        os.replace(old_path, tmp_path)
        tmp_paths.append(tmp_path)

    # Stage 2: rename temporary files to final sequential image names.
    for new_index, tmp_path in enumerate(tmp_paths):
        final_name = f"{prefix}{new_index}{JPG_EXT}"
        final_path = tmp_path.with_name(final_name)
        os.replace(tmp_path, final_path)

    print("Done. Files were reduced and reindexed.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Delete a fraction of frames in a project and reindex remaining files "
            "to a continuous sequence."
        )
    )
    parser.add_argument(
        "project",
        help="Project name inside projects folder, or absolute/relative path to a project directory.",
    )
    parser.add_argument(
        "--projects-folder",
        default="projects",
        help="Base folder for projects when project is provided as a name (default: projects).",
    )
    parser.add_argument(
        "--prefix",
        default="image_",
        help="Image filename prefix (default: image_).",
    )
    parser.add_argument(
        "--delete-fraction",
        default="1/2",
        type=parse_fraction,
        help="Fraction of frames to delete, e.g. 1/2, 2/3, 3/4 (default: 1/2).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without changing files.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt and apply changes immediately.",
    )
    return parser


def resolve_project_path(project_arg: str, projects_folder: str) -> Path:
    project_path = Path(project_arg)
    if project_path.exists():
        return project_path.resolve()
    return (Path(projects_folder) / project_arg).resolve()


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    project_path = resolve_project_path(args.project, args.projects_folder)
    if not project_path.exists():
        parser.error(f"Project path does not exist: {project_path}")
    if not project_path.is_dir():
        parser.error(f"Project path is not a directory: {project_path}")

    delete_num, delete_den = args.delete_fraction
    reduce_project_frames(
        project_dir=project_path,
        prefix=args.prefix,
        delete_num=delete_num,
        delete_den=delete_den,
        dry_run=args.dry_run,
        yes=args.yes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
