import json
import os
from os import path
import platform
import shutil
from typing import Optional

DEFAULT_EDITOR_INSTALL_PATH = "C:/Program Files/Unity/Hub/Editor"


def find_unity_executable(
        preferred_version: Optional[str] = None) -> Optional[str]:
    """Find the path to the unity executable.

    Args:
        preferred_version: The preferred version of Unity to use.

    Returns:
        str: The path to the Unity executable if it was found.
        None: if an executable could not be found.
    """
    system = platform.system()
    if system == "Windows":
        return _find_unity_windows(preferred_version)
    else:
        return _find_unity_posix()


def _find_unity_windows(
        preferred_version: Optional[str] = None) -> Optional[str]:
    appdata_path = os.getenv("APPDATA")
    path_to_unity_hub_data = path.join(appdata_path, "UnityHub")
    secondary_install_loc = path.join(path_to_unity_hub_data,
                                      "secondaryInstallPath.json")

    # check to see if we've configged a secondary install location, if we have
    # then use that to find editor versions
    has_secondary_install = os.stat(secondary_install_loc).st_size > 0
    editor_install_path = DEFAULT_EDITOR_INSTALL_PATH
    if has_secondary_install:
        with open(secondary_install_loc, 'r') as f_handle:
            editor_install_path = json.load(f_handle)

    return _scan_unity_versions(editor_install_path, preferred_version)


def _scan_unity_versions(folder: str,
                         preferred_version: Optional[str] = None
                         ) -> Optional[str]:
    """Scan a folder of unity versions for a specific version."""
    subdirs = [
        path.join(folder, name) for name in os.listdir(folder)
        if path.isdir(path.join(folder, name))
    ]
    if preferred_version is None:
        return path.join(subdirs[0], "Editor", "Unity.exe")
    for editor in subdirs:
        if preferred_version in editor:
            return path.join(editor, "Editor", "Unity.exe")
    return None


def _find_unity_posix() -> Optional[str]:
    # very very naive solution...
    return shutil.which("unity")