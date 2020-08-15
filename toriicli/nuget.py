from dataclasses import dataclass
import logging
import os
from os import path
import pkg_resources
import re
import shutil
import subprocess
from typing import Tuple, List, Optional

import xmltodict

PACKAGE_REGEX = re.compile(r"^([A-Za-z\.-]*)\.(\d+(?:\.\d+){2,3}).*$")
"""Regex to extract a name and version from a NuGet package folder name.
i.e. for Newtonsoft.Json.12.0.1, would extract 'Newtonsoft.Json' 
and '12.0.1'.
Also handles weird versioning, i.e. MoonSharp.2.0.0.0 extracts 'MoonSharp' and
'2.0.0' (leaving out the last zero). Thanks, MoonSharp."""


@dataclass
class NuGetPackage:
    name: str
    version: str
    framework: str


def create_config(config_path: str, exist_ok: bool) -> bool:
    """Create the NuGet config in a given path. Returns None if the file 
    already existed and exist_ok was set to False."""
    os.makedirs(config_path, exist_ok=True)

    nuget_out_file_path = path.join(config_path, "nuget.config")
    if not exist_ok and path.exists(nuget_out_file_path):
        # if it already existed and we're not okay with that then exit early
        return False

    # write the file to the location
    with open(nuget_out_file_path, 'w') as config_file:
        # replace any funky windows line endings that might be in there
        example_cfg = pkg_resources.resource_string(
            "toriicli", "nuget.config").decode("utf-8").replace("\r", "")
        config_file.write(example_cfg)

    packages_out_file_path = path.join(config_path, "packages.config")
    if not exist_ok and path.exists(packages_out_file_path):
        # if it already existed and we're not okay with that then exit early
        return False

    # write the file to the location
    with open(packages_out_file_path, 'w') as config_file:
        # replace any funky windows line endings that might be in there
        example_cfg = pkg_resources.resource_string(
            "toriicli", "packages.config").decode("utf-8").replace("\r", "")
        config_file.write(example_cfg)

    return True


def restore_packages(project_path: str, project_name: str,
                     project_install_path: str) -> bool:
    """Run a NuGet restore for packages in packages.config, and copy them
    all over to the Torii project."""
    # run NuGet restore to download the packages
    success, exit_code = _run_restore(project_path, project_name)
    if not success:
        logging.error(f"nuget restore failed with exit code {exit_code}")
        return False

    # gather info about the packages from the packages config
    packages = _gather_nuget_packages(project_path)

    # copy the downloaded packages into the project
    success = _copy_packages_to_project(project_path, packages,
                                        project_install_path)
    return success


def install_package(project_path: str, package_name: str,
                    version: Optional[str], target_framework: str,
                    project_install_path: str) -> bool:
    """Install a NuGet package to the Torii project."""
    logging.info(f"Attempting to install NuGet package '{package_name}'")

    # first check to see if it's already installed
    if _package_installed(project_path, package_name):
        logging.info(f"Package '{package_name}' was already installed!"
                     " Doing nothing.")
        return True

    # install the package
    success, exit_code = _run_install(project_path, package_name, version)
    if not success:
        logging.error(
            f"nuget install {package_name} failed with exit code {exit_code}")
        return False

    # get the package metadata from the installation
    installed_package = _get_installed_package_data(project_path, package_name,
                                                    target_framework)
    if installed_package is None:
        return False

    # add this package to packages.config
    _add_to_packages_config(project_path, installed_package)

    # now copy the new package into the project
    success = _copy_packages_to_project(project_path, [installed_package],
                                        project_install_path)
    return success


def uninstall_package(project_path: str, package_name: str,
                      project_install_path: str) -> bool:
    """Uninstall a NuGet package from the Torii project."""
    # attempt to get package data from packages.config
    package = _gather_nuget_package(project_path, package_name)
    if package is None:
        logging.error(f"Package '{package_name}' was not installed.")
        return False

    # remove the package from the project
    _remove_package_from_project(project_path, package, project_install_path)

    # remove the package from packages.config
    _remove_from_packages_config(project_path, package)

    return True


def _copy_packages_to_project(project_path: str, packages: List[NuGetPackage],
                              path_in_project: str) -> bool:
    for package in packages:
        # get the path to the package files
        package_files_path = path.join(project_path, "nuget-packages",
                                       f"{package.name}.{package.version}",
                                       "lib", package.framework)

        # get the path within the project
        dst_path = path.join(project_path, "Assets", path_in_project,
                             package.name)

        # remove the package if it already existed
        if path.exists(dst_path):
            shutil.rmtree(dst_path)

        logging.info(
            f"Copying package '{package.name}' to project path {path_in_project}..."
        )

        # copy the package files over
        try:
            shutil.copytree(package_files_path, dst_path)
        except shutil.Error as err:
            logging.error(f"Unable to copy: {err}")
            return False


def _remove_package_from_project(project_path: str, package: NuGetPackage,
                                 path_in_project: str) -> None:
    # get the path within the project
    dst_path = path.join(project_path, "Assets", path_in_project, package.name)

    # remove the package if it existed
    if path.exists(dst_path):
        logging.info(f"Removing package '{package.name}' from project...")
        shutil.rmtree(dst_path)

    # also remove it from the nuget-packages folder if it exists there
    nuget_packages_package_path = path.join(
        project_path, "nuget-packages", f"{package.name}.{package.version}")
    if path.exists(nuget_packages_package_path):
        logging.info(
            f"Removing package '{package.name}' from nuget-packages directory..."
        )
        shutil.rmtree(nuget_packages_package_path)


def _get_installed_package_data(
        project_path: str, package_name: str,
        target_framework: str) -> Optional[NuGetPackage]:
    """Gets package metadata from an installed package.
    Returns NuGetPackage object."""
    package_dir = path.join(project_path, "nuget-packages")
    package_dirs = [
        path.basename(f.path) for f in os.scandir(package_dir) if f.is_dir()
    ]
    installed_packages = [
        pkg for pkg in package_dirs if pkg.startswith(package_name)
    ]
    if len(installed_packages) == 0:
        logging.error(f"Unable to find installed package '{package_name}'")
        return None
    installed_package = installed_packages[0]
    version_match = PACKAGE_REGEX.fullmatch(installed_package)
    package_name = version_match.group(1)
    package_version = version_match.group(2)
    package_path = path.join(package_dir, installed_package)
    package_framework = _find_appropriate_package_target(
        package_path, target_framework)
    if package_framework is None:
        return None

    return NuGetPackage(package_name, package_version, package_framework)


def _find_appropriate_package_target(package_path: str,
                                     target_framework: str) -> Optional[str]:
    """Go through each available target of the package, and try to find the
    a version <= the target version. This will be the latest version we can
    possibly use.
    
    Returns None if there was no version meeting this requirement."""
    package_lib_path = path.join(package_path, "lib")

    # get all targets
    all_targets = [
        path.basename(f.path) for f in os.scandir(package_lib_path)
        if f.is_dir()
    ]

    # filter to just .NET Framework targets
    net_framework_targets = [
        t for t in all_targets
        if t.startswith("net") and "standard" not in t and "core" not in t
    ]

    # check for highest available version <= the target version
    for framework_version_str in reversed(net_framework_targets):
        # remove the 'net'
        framework_version = framework_version_str[3:]

        # remove '-client' if it's there (for .NET client profile)
        if framework_version.endswith("-client"):
            framework_version = framework_version[:-len("-client")]

        # normalize versions like '46' to '460'
        if len(framework_version) < 3:
            to_add = 3 - len(framework_version)
            framework_version += "0" * to_add

        # perform the <= check easily by converting them to ints
        target_num = int(target_framework)
        framework_num = int(framework_version)
        if framework_num <= target_num:
            return framework_version_str

    pkg_name = path.basename(package_path)
    logging.error(f"Unable to find target for package {pkg_name} matching "
                  f"<= {target_framework}")
    return None


def _add_to_packages_config(project_path: str, package: NuGetPackage) -> None:
    """Update the NuGet packages.config file to include a new package."""
    nuget_packages_config = path.join(project_path, "packages.config")
    with open(nuget_packages_config, 'rb') as packages_config:
        parsed = xmltodict.parse(packages_config, force_list=("package"))
    new_package = {
        "@id": package.name,
        "@version": package.version,
        "@targetFramework": package.framework
    }

    # handle empty packages.config
    if parsed["packages"] is None:
        parsed["packages"] = {"package": []}

    parsed["packages"]["package"].append(new_package)
    with open(nuget_packages_config, 'w') as packages_config:
        packages_config.write(xmltodict.unparse(parsed, pretty=True))


def _remove_from_packages_config(project_path: str,
                                 package: NuGetPackage) -> None:
    """Update the NuGet packages.config file to remove a package."""
    nuget_packages_config = path.join(project_path, "packages.config")
    with open(nuget_packages_config, 'rb') as packages_config:
        parsed = xmltodict.parse(packages_config, force_list=("package"))
    package_xml = {
        "@id": package.name,
        "@version": package.version,
        "@targetFramework": package.framework
    }

    parsed["packages"]["package"].remove(package_xml)

    with open(nuget_packages_config, 'w') as packages_config:
        packages_config.write(xmltodict.unparse(parsed, pretty=True))


def _package_installed(project_path: str, package_name: str) -> bool:
    """Check if a package is already installed."""
    return _gather_nuget_package(project_path, package_name) is not None


def _gather_nuget_package(project_path: str,
                          package_name: str) -> Optional[NuGetPackage]:
    """Get a NuGet package from the packages.config file."""
    for pkg in _gather_nuget_packages(project_path):
        if pkg.name == package_name:
            return pkg
    return None


def _gather_nuget_packages(project_path: str) -> List[NuGetPackage]:
    """Parse the NuGet packages.config file in the project to get a list
    of packages."""
    nuget_packages_config = path.join(project_path, "packages.config")
    with open(nuget_packages_config, 'rb') as packages_config:
        parsed = xmltodict.parse(packages_config)

    # if packages.config is empty, return an empty list
    if parsed["packages"] is None:
        return []

    packages = []

    # handle packages.config with only one package
    if isinstance(parsed["packages"]["package"], list):
        for package in parsed["packages"]["package"]:
            nuget_package = NuGetPackage(package["@id"], package["@version"],
                                         package["@targetFramework"])
            packages.append(nuget_package)
    else:
        package = parsed["packages"]["package"]
        nuget_package = NuGetPackage(package["@id"], package["@version"],
                                     package["@targetFramework"])
        packages.append(nuget_package)
    return packages


def _run_restore(project_path: str, project_name: str) -> Tuple[bool, int]:
    """Run a NuGet restore for the project.

    Returns a 2-tuple indicating whether the restore was a success, and the
    exit code of NuGet.
    """
    logging.info(f"Running nuget restore for {project_name}.sln...")

    solution_path = path.join(project_path, f"{project_name}.sln")
    args = ["nuget", "restore", solution_path]
    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    for line in iter(proc.stdout.readline, b""):
        logging.info(f"--> {line.decode('utf-8').rstrip()}")

    proc.wait()

    return proc.returncode == 0, proc.returncode


def _run_install(project_path: str, package_name: str,
                 version: Optional[str]) -> Tuple[bool, int]:
    """Install a NuGet package for the project.

    Returns a 2-tuple indicating whether the install was a success, and the
    exit code of NuGet.
    """
    args = [
        "nuget", "install", package_name, "-SolutionDirectory", project_path
    ]
    if version is not None:
        args += ["-Version", version]
    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    for line in iter(proc.stdout.readline, b""):
        logging.info(f"--> {line.decode('utf-8').rstrip()}")

    proc.wait()

    return proc.returncode == 0, proc.returncode