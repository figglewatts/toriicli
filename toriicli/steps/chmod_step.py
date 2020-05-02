from __future__ import annotations
import functools
import logging
import operator
import os
from os import path
import stat
from typing import List

from . import base_step, schemas


class ChmodStep(base_step.BaseStep):
    def __init__(self, keep: str, context: dict, filter: schemas.StepFilter,
                 file_name: str, permissions: List[str]) -> None:
        super().__init__(keep, context, filter)
        self.file_name = self.template(file_name)
        self.permissions = permissions

    def perform(self) -> bool:
        logging.info("--> Running chmod...")
        path_to_file = path.join(self.workspace, self.file_name)
        st = os.stat(path_to_file)
        stat_vars = vars(stat)
        permissions_bits = [
            stat_vars[permission] for permission in self.permissions
        ]
        permissions = functools.reduce(operator.or_, permissions_bits,
                                       st.st_mode)
        os.chmod(path_to_file, permissions)
