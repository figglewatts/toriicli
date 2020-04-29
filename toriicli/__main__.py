import click

VERSION = "#{TAG_NAME}#"

from .build import detect_unity


@click.group()
@click.version_option(version=VERSION)
def toriicli():
    pass


@toriicli.command()
def hello():
    print(detect_unity.find_unity_executable("2017.4.30f1"))


def main():
    toriicli()


if __name__ == "__main__":
    main()