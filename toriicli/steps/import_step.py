from __future__ import annotations
import logging
import os
from os import path
import shutil

from . import base_step, schemas
from ..storage import make_provider


class ImportStep(base_step.BaseStep):
    def __init__(self, keep: str, context: dict, filter: schemas.StepFilter,
                 **kwargs) -> None:
        super().__init__(keep, context, filter)
        backend = kwargs.pop("backend", None)
        if backend is None:
            raise ValueError(
                "Missing 'backend' in 'using' section of import step")
        for k, v in kwargs.items():
            kwargs[k] = self.template(v)
        self.provider = make_provider(backend, **kwargs)

    def perform(self) -> bool:
        logging.info("--> Running import...")
        for obj in self.provider.ls():
            file_path = path.join(self.workspace, obj)
            self.provider.retrieve(obj, file_path)
        return True