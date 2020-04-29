from dataclasses import dataclass

from marshmallow import Schema, fields
import yaml


class ToriiCliConfigSchema(Schema):
    """Marshmallow schema for app config."""
    unity_executable_path = fields.Str(required=False, missing=None)
    unity_preferred_version = fields.Str(required=False, missing=None)


@dataclass
class ToriiCliConfig:
    """The config of the app. For details on each field, please see
    example_config.yml in the package."""
    unity_executable_path: str
    unity_preferred_version: str