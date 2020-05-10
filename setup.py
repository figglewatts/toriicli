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
        "appdirs==1.4.3",
        "boto3==1.13.6",
        "botocore==1.16.6",
        "click==7.1.2",
        "docutils==0.15.2",
        "future==0.18.2",
        "jinja2==2.11.2",
        "jmespath==0.9.5",
        "markupsafe==1.1.1",
        "marshmallow==3.6.0",
        "pefile==2019.4.18",
        "python-dateutil==2.8.1",
        "python-dotenv==0.13.0",
        "pyyaml==5.3.1",
        "s3transfer==0.3.3",
        "six==1.14.0",
        "urllib3==1.25.9; python_version != '3.4'",
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
    package_data={"toriicli": ["example_config.yml"]},
)
