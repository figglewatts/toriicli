from dataclasses import dataclass
import logging
import os
from os import path
from typing import List, Optional

import pefile

from .build_def import BuildDef

BUILD_NUMBER_FILENAME = "buildnumber.txt"


@dataclass
class BuildData:
    build_def: BuildDef
    build_number: str
    path: str


def _get_assembly_path(build_def: BuildDef) -> Optional[str]:
    """Get the path to Assembly-CSharp.dll within the build output folder.
    
    Returns None if target was not supported.
    """
    if "Windows" in build_def.target or "Linux" in build_def.target:
        exe_name_sans_extension = build_def.executable_name.rsplit(".", 1)[0]
        return path.join(build_def.target, f"{exe_name_sans_extension}_Data",
                         "Managed", "Assembly-CSharp.dll")
    elif "OSX" in build_def.target:
        return path.join(build_def.target, f"{build_def.executable_name}",
                         "Contents", "Resources", "Data", "Managed",
                         "Assembly-CSharp.dll")
    else:
        logging.error(f"Build target: {build_def.target} is not supported!")
        return None


def _get_build_number(build_folder: str, build_def: BuildDef) -> Optional[str]:
    """Get the build number of a completed build by inspecting the produced
    assembly.

    Will return None if an error occurred.
    """
    assembly_path = _get_assembly_path(build_def)
    if assembly_path is None:
        return None

    assembly_path = path.join(build_folder, assembly_path)

    # we're going whole-hog here and loading the PE file itself to figure out
    # the version number... writing it to a TXT file during the Unity build
    # wasn't producing consistent version numbers as it seemed to be building
    # the assembly twice and only writing the number after the first build
    try:
        pe = pefile.PE(assembly_path)
        ver_info = pe.VS_FIXEDFILEINFO[0]
        ver_ms = ver_info.ProductVersionMS
        ver_ls = ver_info.ProductVersionLS
        major = ver_ms >> 16  # version numbers are 2 bytes each - grab em like this
        minor = ver_ms & 0xFFFF
        build = ver_ls >> 16
        patch = ver_ls & 0xFFFF
        return f"{major}.{minor}.{build}.{patch}"
    except OSError as err:
        logging.error(f"Could not open built assembly: {err}")
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
    build_number = _get_build_number(build_folder, build_def)
    if build_number is None:
        return None

    # and that's all, folks
    return BuildData(build_def, build_number, build_path)