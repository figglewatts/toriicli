"""setup.py

Used for installing toriicli via pip.
"""
from setuptools import setup, find_packages


def repo_file_as_string(file_path: str) -> str:
    with open(file_path, "r") as repo_file:
        return repo_file.read()


setup(
    dependency_links=[],
    install_requires=["click==7.1.2", "marshmallow==3.5.1", "pyyaml==5.3.1"],
    name="toriicli",
    version="#{TAG_NAME}#",
    description="CLI utility for Torii",
    long_description=repo_file_as_string("README.md"),
    long_description_content_type="text/markdown",
    author="Figglewatts",
    author_email="me@figglewatts.co.uk",
    packages=find_packages("."),
    entry_points="""
        [console_scripts]
        toriicli=toriicli.__main__:toriicli
    """,
    python_requires=">=3.7",
    include_package_data=True,
    package_data={"toriicli": ["example_config.yml"]},
)
