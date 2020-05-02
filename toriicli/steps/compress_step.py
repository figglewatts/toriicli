from __future__ import annotations
import logging
from os import path
import shutil
import tempfile

from . import base_step, schemas


class CompressStep(base_step.BaseStep):
    def __init__(self, keep: str, context: dict, filter: schemas.StepFilter,
                 archive_name: str, format: str) -> None:
        super().__init__(keep, context, filter)
        self.archive_name = self.template(archive_name)
        self.format = format

    def perform(self) -> bool:
        logging.info("--> Running compress...")
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = shutil.make_archive(path.join(
                temp_dir, self.archive_name),
                                               self.format,
                                               root_dir=self.workspace)
            archive_name = path.basename(archive_path)
            shutil.copy(path.join(temp_dir, archive_name),
                        path.join(self.workspace, archive_name))
