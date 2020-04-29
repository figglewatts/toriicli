import click
from dataclasses import dataclass
import os

VERSION = "#{TAG_NAME}#"

from .build import detect_unity
from . import config


@dataclass
class ToriiCliContext:
    cfg: config.ToriiCliConfig
    project_path: str


pass_ctx = click.make_pass_decorator(ToriiCliContext)

SUBCOMMANDS_DONT_LOAD_CONFIG = ["new"]
"""These subcommands shouldn't load config -- it may not exist beforehand."""


@click.group()
@click.version_option(version=VERSION)
@click.option("--project-path",
              "-p",
              required=False,
              type=str,
              default=os.getcwd(),
              help="The project directory. Defaults to CWD if not given.")
@click.pass_context
def toriicli(ctx, project_path):
    """CLI utility for the Unity Torii framework."""
    if ctx.invoked_subcommand not in SUBCOMMANDS_DONT_LOAD_CONFIG:
        cfg = config.from_yaml(config.CONFIG_NAME)
        if cfg is None:
            raise SystemExit(1)
        ctx.obj = ToriiCliContext(cfg, project_path)


@toriicli.command()
@click.argument("version", nargs=1, default=None, required=False)
def unity(version):
    """Print the path to the Unity executable. You can optionally specify a
    specific Unity VERSION to attempt to find."""
    exe_path = detect_unity.find_unity_executable(version)
    if exe_path is not None:
        print(exe_path)
    else:
        raise SystemExit(1)


@toriicli.command()
@click.argument("project_path", nargs=1, default=None, required=False)
def new(project_path):
    """Create a new Torii project in PROJECT_PATH. If not specified, will use
    the current working directory as the project path."""
    out_file_path = config.create_config(project_path)
    print(f"Created new Torii project: {out_file_path}")