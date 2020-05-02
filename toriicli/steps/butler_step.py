from __future__ import annotations
import logging
from os import path
import subprocess
from typing import List, Optional

from . import base_step, schemas


class ButlerStep(base_step.BaseStep):
    def __init__(self,
                 keep: str,
                 context: dict,
                 filter: schemas.StepFilter,
                 directory: str,
                 user: str,
                 game: str,
                 channel: str,
                 user_version: Optional[str] = None) -> None:
        super().__init__(keep, context, filter)
        self.directory = path.join(self.workspace, self.template(directory))
        self.user = self.template(user)
        self.game = self.template(game)
        self.channel = self.template(channel)
        self.user_version = self.template(user_version)

    def perform(self) -> bool:
        logging.info("--> Running butler...")
        butler_args = [
            "butler", "push", self.directory,
            f"{self.user}/{self.game}:{self.channel}"
        ]
        if self.user_version is not None:
            butler_args += ["--userversion", self.user_version]
        proc = subprocess.Popen(butler_args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        for line in iter(proc.stdout.readline, b""):
            logging.info(f"--> {line.decode('utf-8').rstrip()}")

        proc.wait()
        return True