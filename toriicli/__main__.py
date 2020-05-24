from dataclasses import dataclass
import logging
import logging.config
import os
from os import path
import shutil
from typing import List, Optional

import click
import dotenv

from .build import detect_unity, build_def, unity, build_data
from . import steps, config
from . import nuget as _nuget

VERSION = "#{TAG_NAME}#"


class ToriiCliContext:
    def __init__(self, cfg: config.ToriiCliConfig, project_path: str) -> None:
        self.cfg = cfg

        # if the project path is not absolute, we need to make it so, as
        # Unity expects it to be absolute
        if not path.isabs(project_path):
            project_path = path.abspath(project_path)

        self.project_path = project_path
        self.project_name = path.basename(project_path)


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
    """CLI utility for the Unity Torii library."""
    config.setup_logging()
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
    nuget_out_file_path = _nuget.create_config(project_path, exist_ok=force)

    if out_file_path is None or nuget_out_file_path is False:
        logging.error(
            f"Could not create project in {project_path}, "
            f"Some required files already existed. If you wanted this and are "
            "okay with these files being overwritten, try running again with "
            "--force.")
        raise SystemExit(1)

    logging.info(f"Created new Torii project: {out_file_path}")


@toriicli.command()
@click.option(
    "--option",
    "-o",
    help="Will run post-steps with this option in the filter. Allows multiple.",
    multiple=True)
@click.option("--no-unity", is_flag=True, help="Don't run the Unity build.")
@click.option("--no-clean", is_flag=True, help="Don't clean up afterwards.")
@pass_ctx
def build(ctx: ToriiCliContext, option: List[str], no_unity: bool,
          no_clean: bool):
    """Build a Torii project."""
    dotenv.load_dotenv()  # for loading credentials

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
    if not no_unity:
        builder = unity.UnityBuilder(exe_path)
        success, exit_code = builder.build(ctx.project_path,
                                           ctx.cfg.unity_build_execute_method)
        if not success:
            logging.critical(f"Unity failed with exit code: {exit_code}")
            raise SystemExit(1)

        logging.info("Build success")

    logging.info("Collecting completed builds...")

    # now, collect info on the completed builds (build number etc.), and
    # run post-steps
    for bd in ctx.cfg.build_defs:
        output_folder = path.join(ctx.project_path,
                                  ctx.cfg.build_output_folder)
        build_info = build_data.collect_finished_build(output_folder, bd)
        if build_info is None:
            logging.error(f"Unable to find build for target {bd.target}")
            continue

        logging.info(f"Found version {build_info.build_number} for target "
                     f"{build_info.build_def.target} at {build_info.path}")

        # build steps implicitly have an import step as the first step, to
        # import the files from the build directory into the workspace
        steps_to_run = [
            steps.import_step.ImportStep("**",
                                         vars(build_info),
                                         None,
                                         backend="local",
                                         container=build_info.path)
        ]

        # get the steps we're running for this build def, based on the filters
        try:
            logging.info("Collecting post-steps...")
            for step in ctx.cfg.build_post_steps:
                if step.filter is None or step.filter.match(bd, option):
                    steps_to_run.append(
                        step.get_implementation(vars(build_info)))

            logging.info("Running post-steps for build...")
            # now run each of the steps
            for i, step in enumerate(steps_to_run):
                # make sure we import the workspace of the step before this
                if i != 0:
                    step.use_workspace(steps_to_run[i - 1])

                step.perform()
        finally:
            # now clean up all the steps we ran
            [step.cleanup() for step in steps_to_run]
            logging.info("Finished running post steps! Build complete")

    # clean up after the build, remove build defs and build output folder
    if not no_clean:
        try:
            build_def.remove_generated_build_defs(ctx.project_path)
            shutil.rmtree(path.join(ctx.project_path,
                                    ctx.cfg.build_output_folder),
                          ignore_errors=True)
        except OSError:
            logging.exception("Unable to clean up after build")
            raise SystemExit(1)


@toriicli.command()
@click.argument("version", nargs=1, type=str)
@click.option("--target",
              "-t",
              help="Only release specific targets. Allows multiple.",
              multiple=True)
@click.option(
    "--option",
    "-o",
    help="Will run steps with this option in the filter. Allows multiple.",
    multiple=True)
@pass_ctx
def release(ctx: ToriiCliContext, version: str, target: List[str],
            option: List[str]):
    """Release VERSION of Torii project."""
    dotenv.load_dotenv()  # for loading credentials

    logging.info(f"Releasing version {version}")

    # we want to release each build definition defined
    for bd in ctx.cfg.build_defs:
        # skip this build def if it's not defined in the option
        if len(target) > 0 and bd.target not in target:
            continue

        logging.info(f"Running release for target {bd.target}")

        step_context = {"build_number": version, "build_def": bd}
        steps_to_run = []
        try:
            logging.info("Collecting steps...")

            for step in ctx.cfg.release_steps:
                if step.filter is None or step.filter.match(bd, option):
                    steps_to_run.append(step.get_implementation(step_context))

            logging.info("Running steps for release...")
            # now run each of the steps
            for i, step in enumerate(steps_to_run):
                # make sure we import the workspace of the step before this
                if i != 0:
                    step.use_workspace(steps_to_run[i - 1])

                step.perform()
        finally:
            # now clean up all the steps we ran
            [step.cleanup() for step in steps_to_run]
            logging.info("Finished running steps! Release complete")


@toriicli.group()
@pass_ctx
def nuget(ctx: ToriiCliContext):
    """Manage NuGet packages for project."""


@nuget.command()
@pass_ctx
def restore(ctx: ToriiCliContext):
    """Run a NuGet restore for this project."""
    success = _nuget.restore_packages(ctx.project_path, ctx.project_name,
                                      ctx.cfg.nuget_package_install_path)
    raise SystemExit(0 if success else 1)


@nuget.command()
@click.argument("package", nargs=1, type=str)
@click.option(
    "--version",
    "-v",
    nargs=1,
    type=str,
    default=None,
    help=
    "The version of the package to install. If not present, installs latest.")
@pass_ctx
def install(ctx: ToriiCliContext, package: str, version: Optional[str]):
    """Install a NuGet package to this project."""
    success = _nuget.install_package(ctx.project_path, package, version,
                                     ctx.cfg.unity_dotnet_framework_version,
                                     ctx.cfg.nuget_package_install_path)
    raise SystemExit(0 if success else 1)


@nuget.command()
@click.argument("package", nargs=1, type=str)
@pass_ctx
def uninstall(ctx: ToriiCliContext, package: str):
    """Uninstall a NuGet package from this project."""
    success = _nuget.uninstall_package(ctx.project_path, package,
                                       ctx.cfg.nuget_package_install_path)
    raise SystemExit(0 if success else 1)
