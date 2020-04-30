from dataclasses import dataclass
import logging
import os
from os import path
from typing import List, Optional

from .build_def import BuildDef

BUILD_NUMBER_FILENAME = "buildnumber.txt"


@dataclass
class BuildData:
    build_def: BuildDef
    build_number: str
    path: str


def _get_build_number(build_path: str) -> Optional[str]:
    """Attempt to get the build number from a completed build, returns the 
    build number (as a str) or None if an error occurred."""
    path_to_build_number = path.join(build_path, BUILD_NUMBER_FILENAME)
    try:
        with open(path_to_build_number, 'r') as build_num_file:
            return build_num_file.read()
    except OSError:
        logging.exception(f"Unable to open {path_to_build_number}")
        return None


def collect_finished_build(build_folder: str,
                           build_def: BuildDef) -> Optional[BuildData]:
    """Collect some data about a completed build, using the build def and
    reading files that are in the output directory."""
    # let's make sure it all exists first
    build_path = path.join(build_folder, build_def.target)
    if not path.exists(build_path):
        logging.critical(f"Build path {build_path} did not exist")
        return None
    if len(os.listdir(build_path)) == 0:
        logging.critical(f"Build path {build_path} was empty")
        return None

    # now let's grab the build number
    build_number = _get_build_number(build_path)
    if build_number is None:
        return None

    # and that's all, folks
    return BuildData(build_def, build_number, build_path)