from __future__ import annotations
from abc import ABC, abstractmethod
import glob
import tempfile
from typing import Mapping, Any
import os
from os import path
import shutil

from jinja2 import Template

from . import schemas


class BaseStep(ABC):
    """A step transforms some files in a certain way.

    Files are stored in a temporary directory.

    Attributes:
        context: The context to be used when templating input values.
        filter: The conditions upon which this step should be run.
        workspace: The TemporaryDirectory used to store this step's files.
    """
    def __init__(self, keep: str, context: dict,
                 filter: schemas.StepFilter) -> None:
        self.workspace = tempfile.mkdtemp()
        self.context = context
        self.keep = self.template(keep)
        self.filter = filter

    @abstractmethod
    def perform(self) -> bool:
        """Perform this step."""
        raise NotImplementedError()

    def cleanup(self) -> None:
        """Clean up after running this step. Deletes the workspace."""
        shutil.rmtree(self.workspace)

    def template(self, string: str) -> str:
        """Template a string using this step's context."""
        if string is None:
            return None
        expanded_vars = path.expandvars(string)
        return Template(expanded_vars).render(**self.context)

    def use_workspace(self, step: BaseStep) -> None:
        """Copy things from the workspace of another step into this step.
        Will filter based on glob pattern in self.keep.
        """
        glob_expr = path.join(step.workspace, self.keep)
        for file in glob.iglob(glob_expr):
            path_in_workspace = path.relpath(file, step.workspace)
            path_in_new_workspace = path.join(self.workspace,
                                              path_in_workspace)

            if path_in_workspace == ".":
                continue

            if path.isdir(file):
                shutil.copytree(file, path_in_new_workspace)
            else:
                shutil.copy(file, path_in_new_workspace)
