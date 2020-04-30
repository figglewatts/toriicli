from dataclasses import dataclass
import logging
import logging.config
import os
from os import path
import shutil

import click
import dotenv

from .build import detect_unity, build_def, unity, build_data
from . import config

VERSION = "#{TAG_NAME}#"


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
    config.setup_logging()
    dotenv.load_dotenv()  # for loading credentials
    if ctx.invoked_subcommand not in SUBCOMMANDS_DONT_LOAD_CONFIG:
        cfg = config.from_yaml(config.CONFIG_NAME)
        if cfg is None:
            raise SystemExit(1)
        ctx.obj = ToriiCliContext(cfg, cfg.actual_project_dir or project_path)


@toriicli.command()
@click.argument("version", nargs=1, default=None, required=False)
@pass_ctx
def find(ctx: ToriiCliContext, version):
    """Print the path to the Unity executable. You can optionally specify a
    specific Unity VERSION to attempt to find."""
    exe_path = detect_unity.find_unity_executable(
        version or ctx.cfg.unity_preferred_version)
    if exe_path is not None:
        logging.info(exe_path)
    else:
        raise SystemExit(1)


@toriicli.command()
@click.argument("project_path", nargs=1, default=os.getcwd(), required=False)
@click.option("--force",
              "-f",
              is_flag=True,
              help="Create the project even if one already existed.")
def new(project_path, force):
    """Create a new Torii project in PROJECT_PATH. If not specified, will use
    the current working directory as the project path. Will not overwrite an
    existing project."""
    out_file_path = config.create_config(project_path, exist_ok=force)

    if out_file_path is None:
        logging.error(
            f"Could not create project in {project_path}, "
            f"{config.CONFIG_NAME} already existed. If you wanted this, try "
            "running again with --force.")
        raise SystemExit(1)

    logging.info(f"Created new Torii project: {out_file_path}")


@toriicli.command()
@pass_ctx
def build(ctx: ToriiCliContext):
    """Build a Torii project."""
    # first, make sure we can find the Unity executable
    logging.info("Finding Unity executable...")
    exe_path = ctx.cfg.unity_executable_path or detect_unity.find_unity_executable(
        ctx.cfg.unity_preferred_version)
    if exe_path is None:
        logging.critical("Unable to find Unity executable.")
        raise SystemExit(1)
    if not path.exists(exe_path):
        logging.critical(f"Unity executable not found at: {exe_path}")
        raise SystemExit(1)
    logging.info(f"Found Unity at: {exe_path}")

    # now, generate the build_defs so Unity can build from them
    logging.info(f"Generating {build_def.BUILD_DEFS_FILENAME}...")
    success = build_def.generate_build_defs(ctx.project_path,
                                            ctx.cfg.build_output_folder,
                                            ctx.cfg.build_defs)
    if not success:
        raise SystemExit(1)

    # run Unity to build game
    builder = unity.UnityBuilder(exe_path)
    success, exit_code = builder.build(ctx.project_path,
                                       ctx.cfg.unity_build_execute_method)
    if not success:
        logging.critical(f"Unity failed with exit code: {exit_code}")
        raise SystemExit(1)

    # now, collect info on the completed builds (build number etc.), and
    # run post-steps
    for bd in ctx.cfg.build_defs:
        build_info = build_data.collect_finished_build(
            ctx.cfg.build_output_folder, bd)

        # running post steps:
        # iterate through and get list of all post steps for which this
        #   build def will pass the filter
        # create a temporary dir for each step with
        # step has:
        #   - read dir: where it operates on
        #   - optional temporary write dir: where it writes to
        #       https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory

    # clean up after the build, remove build defs and build output folder
    try:
        build_def.remove_generated_build_defs(ctx.project_path)
        shutil.rmtree(ctx.cfg.build_output_folder)
    except OSError:
        logging.exception("Unable to clean up after build")
        raise SystemExit(1)