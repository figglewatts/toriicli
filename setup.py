"""setup.py

Used for installing toriicli via pip.
"""
from setuptools import setup, find_packages


def repo_file_as_string(file_path: str) -> str:
    with open(file_path, "r") as repo_file:
        return repo_file.read()


setup(
    dependency_links=[],
    install_requires=[
        "pyyaml>=5.3.1",
        "marshmallow>=3.6.0",
        "click>=7.1.2",
        "python-dotenv>=0.13.0",
        "boto3>=1.13.16",
        "jinja2>=2.11.2",
        "pefile>=2019.4.18",
        "xmltodict>=0.12.0",
    ],
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
    package_data={
        "toriicli": ["example_config.yml", "nuget.config", "packages.config"]
    },
)
