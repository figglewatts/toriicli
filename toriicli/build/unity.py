import logging
from os import path
import subprocess
from typing import Tuple

UNITY_ARGS = "-batchmode -nographics -quit -logFile - " + \
    "-executeMethod {execute_method} -projectPath {project_path}"
"""The args to give to Unity to build from the command line. Needs execute_method
and project_path to be substituted in via a .format()."""


def build_args(execute_method: str, project_path: str) -> str:
    """Build the command-line args to supply to Unity."""
    return UNITY_ARGS.format(execute_method=execute_method,
                             project_path=project_path)


class UnityBuilder:
    """Encapsulates using the Unity executable to build projects with Torii.

    Attributes:
        executable_path (str): The path to the Unity executable.
    """
    def __init__(self, executable_path: str) -> None:
        self._ensure_executable_exists(executable_path)
        self.executable_path = executable_path

    def build(self, project_path: str,
              execute_method: str) -> Tuple[bool, int]:
        """Attempt to build a project at a given path.

        Returns a 2-tuple indicating whether the build was a success, and the
        exit code of Unity.
        """
        unity_args = build_args(execute_method, project_path)
        logging.info(f"Running Unity with args: '{unity_args}'")
        proc = subprocess.Popen([self.executable_path] + unity_args.split(" "),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        for line in iter(proc.stdout.readline, b""):
            logging.info(f"--> {line.decode('utf-8').rstrip()}")

        proc.wait()

        return proc.returncode == 0, proc.returncode

    def _ensure_executable_exists(self, executable_path: str):
        if not path.exists(executable_path):
            raise ValueError(
                f"Unable to find Unity executable at {executable_path}")
