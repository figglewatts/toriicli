from dataclasses import dataclass
from typing import Mapping, Any, List

from marshmallow import Schema, fields, post_load, validate

STEPS_IMPL = {"compress": None, "upload": None}


@dataclass
class StepFilter:
    targets: List[str]


class StepFilterSchema(Schema):
    targets = fields.List(fields.Str, required=True, allow_none=False)

    @post_load
    def make_step_filter(self, data, **kwargs):
        return StepFilter(**data)


@dataclass
class Step:
    step: str
    filter: StepFilter
    using: Mapping[str, Any]


class StepSchema(Schema):
    step = fields.Str(required=True,
                      allow_none=False,
                      validate=validate.OneOf(STEPS_IMPL.keys()))
    filter = fields.Nested(StepFilterSchema,
                           required=False,
                           allow_none=False,
                           missing=None)
    using = fields.Mapping(keys=fields.Str,
                           values=fields.Raw,
                           required=False,
                           allow_none=False,
                           missing={})

    @post_load
    def make_step(self, data, **kwargs):
        return Step(**data)