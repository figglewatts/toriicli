from dataclasses import dataclass

from marshmallow import Schema, fields, validate, post_load

VALID_BUILD_TARGETS = [
    "StandaloneOSX", "StandaloneWindows", "iOS", "Android",
    "StandaloneWindows64", "WebGL", "WSAPlayer", "StandaloneLinux64", "PS4",
    "XboxOne", "tvOS", "Switch"
]


class BuildDefSchema(Schema):
    target = fields.Str(required=True,
                        allow_none=False,
                        validate=validate.OneOf(VALID_BUILD_TARGETS))
    executable_name = fields.Str(required=True,
                                 allow_none=False,
                                 validate=validate.Length(min=1))

    def __init__(self,
                 titlecase_field_names: bool = False,
                 *args,
                 **kwargs) -> None:
        self.titlecase_field_names = titlecase_field_names
        super().__init__(*args, **kwargs)

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