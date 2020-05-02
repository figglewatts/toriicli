from __future__ import annotations

from . import base_step, schemas


class CompressStep(base_step.BaseStep):
    def __init__(self,
                 keep: str,
                 context: dict,
                 filter: schemas.StepFilter,
                 archive_name: str,
                 keep_existing: bool = False) -> None:
        super().__init__(keep, context, filter)
        self.archive_name = self.template(archive_name)
        self.keep_existing = keep_existing

    def perform(self) -> bool:
        pass