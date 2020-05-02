from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any, List

from marshmallow import Schema, fields, post_load, validate

from . import base_step, factory
from ..build import build_def


@dataclass
class StepFilter:
    targets: List[str]
    options: List[str]

    def match(self, bd: build_def.BuildDef, options: List[str]) -> bool:
        return (True if self.targets is None else bd.target in self.targets) \
            and (True if self.options is None else set(self.options) <= set(options))


class StepFilterSchema(Schema):
    targets = fields.List(fields.Str,
                          required=False,
                          allow_none=False,
                          missing=None)
    options = fields.List(fields.Str,
                          required=False,
                          allow_none=False,
                          missing=None)

    @post_load
    def make_step_filter(self, data, **kwargs):
        return StepFilter(**data)


@dataclass
class Step:
    step: str
    filter: StepFilter
    using: Mapping[str, Any]
    keep: str

    def get_implementation(self, context: dict) -> base_step.BaseStep:
        """Get this step's implementation."""
        return factory.make_step(self.step, self.keep, context, self.filter,
                                 self.using)


class StepSchema(Schema):
    step = fields.Str(required=True, allow_none=False)
    filter = fields.Nested(StepFilterSchema,
                           required=False,
                           allow_none=False,
                           missing=None)
    using = fields.Mapping(keys=fields.Str,
                           values=fields.Raw,
                           required=False,
                           allow_none=False,
                           missing={})
    keep = fields.Str(required=False, allow_none=False, missing="**")

    @post_load
    def make_step(self, data, **kwargs):
        return Step(**data)