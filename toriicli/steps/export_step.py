from __future__ import annotations
import logging
import os
from os import path

from . import base_step, schemas
from ..storage import make_provider


class ExportStep(base_step.BaseStep):
    def __init__(self, keep: str, context: dict, filter: schemas.StepFilter,
                 **kwargs) -> None:
        super().__init__(keep, context, filter)
        backend = kwargs.pop("backend", None)
        if backend is None:
            raise ValueError(
                "Missing 'backend' in 'using' section of import step")
        self.provider = make_provider(backend, **kwargs)

    def perform(self) -> bool:
        logging.info("--> Running export...")
        for root, _, files in os.walk(self.workspace):
            for file in files:
                file_path = path.join(root, file)
                key = path.relpath(file_path, start=self.workspace)
                with open(file_path, 'rb') as file_handle:
                    self.provider.store(file_handle, key)
        return True