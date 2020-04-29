import click

VERSION = "#{TAG_NAME}#"


@click.group()
@click.version_option(version=VERSION)
def toriicli():
    pass


@toriicli.command()
def hello():
    print("Hello")


def main():
    toriicli()


if __name__ == "__main__":
    main()