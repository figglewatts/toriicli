from __future__ import annotations
from typing import Mapping, Any

from . import schemas, import_step, export_step, compress_step, base_step, chmod_step, butler_step

STEPS_IMPL = {
    "import": import_step.ImportStep,
    "export": export_step.ExportStep,
    "compress": compress_step.CompressStep,
    "chmod": chmod_step.ChmodStep,
    "butler": butler_step.ButlerStep
}


def make_step(step_name: str, keep: str, context: dict,
              filter: schemas.StepFilter,
              using: Mapping[str, Any]) -> base_step.BaseStep:
    """Make a step, given its name and values."""
    try:
        return STEPS_IMPL[step_name](keep, context, filter, **using)
    except KeyError:
        raise ValueError(f"Step name '{step_name}' not recognized!")