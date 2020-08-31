from dataclasses import dataclass
import json
import logging
import os
from os import path
from typing import List

from marshmallow import Schema, fields, validate, post_load, pre_dump

VALID_BUILD_TARGETS = [
    "StandaloneOSXUniversal", "StandaloneOSX", "StandaloneWindows", "iOS",
    "Android", "StandaloneWindows64", "WebGL", "WSAPlayer",
    "StandaloneLinux64", "StandaloneLinuxUniversal", "PS4", "XboxOne", "tvOS",
    "Switch"
]
"""The valid targets for a Unity build, 
from: https://docs.unity3d.com/ScriptReference/BuildTarget.html"""

BUILD_DEFS_FILENAME = "build_defs.json"
"""The filename to save build defs to when building."""


class BuildDefSchema(Schema):
    target = fields.Str(required=True,
                        allow_none=False,
                        validate=validate.OneOf(VALID_BUILD_TARGETS))
    executable_name = fields.Str(required=True,
                                 allow_none=False,
                                 validate=validate.Length(min=1))
    build_folder = fields.Str(required=False, allow_none=False, missing=None)

    def __init__(self,
                 titlecase_field_names: bool = False,
                 build_folder: str = None,
                 *args,
                 **kwargs) -> None:
        self.titlecase_field_names = titlecase_field_names
        self.build_folder = build_folder
        super().__init__(*args, **kwargs)

    @pre_dump(pass_many=True)
    def inject_build_folder(self, data, many, **kwargs):
        """If the build folder is set, we want to inject it into the data."""
        if self.build_folder:
            if many:
                for build_def in data:
                    build_def.build_folder = self.build_folder
            else:
                data.build_folder = self.build_folder
        return data

    def _titlecase(self, string: str) -> str:
        return string.title().replace("_", "")

    def on_bind_field(self, field_name, field_obj):
        if self.titlecase_field_names:
            field_obj.data_key = self._titlecase(field_name
                                                 or field_obj.data_key)

    @post_load
    def make_build_def(self, data, **kwargs):
        return BuildDef(**data)


@dataclass
class BuildDef:
    target: str
    executable_name: str
    build_folder: str


def generate_build_defs(project_path: str, build_folder: str,
                        build_defs: List[BuildDef]) -> bool:
    """Generate a project's build defs in the project path. Returns a bool
    indicating whether generation was successful or not."""
    schema = BuildDefSchema(titlecase_field_names=True,
                            build_folder=build_folder,
                            many=True)
    build_defs_data = schema.dump(build_defs)
    build_defs_path = path.join(project_path, BUILD_DEFS_FILENAME)
    try:
        with open(build_defs_path, 'w') as build_defs_file:
            json.dump(build_defs_data, build_defs_file)
            return True
    except TypeError:
        # if there was some error in the data
        logging.exception(f"Unable to generate {build_defs_path}")
        return False
    except OSError:
        # there was some error in the filesystem
        logging.exception(f"Unable to write build defs")
        return False


def remove_generated_build_defs(project_path: str) -> None:
    build_defs_path = path.join(project_path, BUILD_DEFS_FILENAME)
    if path.exists(build_defs_path):
        os.remove(build_defs_path)