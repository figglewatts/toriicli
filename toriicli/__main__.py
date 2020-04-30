import click
from dataclasses import dataclass
import logging
import logging.config
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

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
"""Context settings for Click CLI."""


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(VERSION, "--version", "-v")
@click.option("--project-path",
              "-p",
              required=False,
              type=str,
              default=os.getcwd(),
              show_default=True,
              help="The project directory.")
@click.pass_context
def toriicli(ctx, project_path):
    """CLI utility for the Unity Torii framework."""
    if ctx.invoked_subcommand not in SUBCOMMANDS_DONT_LOAD_CONFIG:
        config.setup_logging()
        cfg = config.from_yaml(config.CONFIG_NAME)
        if cfg is None:
            raise SystemExit(1)
        ctx.obj = ToriiCliContext(cfg, project_path)


@toriicli.command()
@click.argument("version", nargs=1, default=None, required=False)
@pass_ctx
def unity(ctx: ToriiCliContext, version):
    """Print the path to the Unity executable. You can optionally specify a
    specific Unity VERSION to attempt to find."""
    exe_path = detect_unity.find_unity_executable(
        version or ctx.cfg.unity_preferred_version)
    if exe_path is not None:
        logging.info(exe_path)
    else:
        raise SystemExit(1)


@toriicli.command()
@click.argument("project_path", nargs=1, default=None, required=False)
@pass_ctx
def new(ctx: ToriiCliContext, project_path):
    """Create a new Torii project in PROJECT_PATH. If not specified, will use
    the current working directory as the project path."""
    out_file_path = config.create_config(project_path)
    logging.info(f"Created new Torii project: {out_file_path}")