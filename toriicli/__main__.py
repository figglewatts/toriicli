import click

VERSION = "#{TAG_NAME}#"

from .build import detect_unity
from . import config


@click.group()
@click.version_option(version=VERSION)
def toriicli():
    pass


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


def main():
    toriicli()


if __name__ == "__main__":
    main()