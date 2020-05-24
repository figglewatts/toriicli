# toriicli
[![PyPI version fury.io](https://badge.fury.io/py/toriicli.svg)](https://pypi.python.org/pypi/toriicli/)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
![CI build](https://github.com/figglewatts/toriicli/workflows/CI/badge.svg)
![CD build](https://github.com/figglewatts/toriicli/workflows/CD/badge.svg)

CLI utility for Torii, mainly used for automation of building/releasing
projects.

Torii is a framework for Unity that fills some gaps in its functionality
that I've found over the years.

## Installation
```bash
$ pip install toriicli
```

## Prerequisites
- Python 3.7+
- Unity, installed via Unity Hub
- NuGet and MSBuild (if you want to use the NuGet subcommand)

## Main functionality
`toriicli` has commands for the following:
- `build`: Build a Torii project
- `find`: Find an installation of Unity
- `new`: Create a new Torii project
- `release`: Release a Torii project
- `nuget`: Manage NuGet packages for project

## Common options
- `-p, --project-path`: The path to the `toriiproject.yml` file of the project.
  If you don't specify this it defaults to the current working directory.

## Projects
A `toriicli` project is a directory with a file called `toriiproject.yml`.
The `toriiproject.yml` file is a file containing the configuration for that
project. 

Please see `./toriicli/example_config.yml` for information on how to configure
`toriicli`.

Running `toriicli new` in a directory will create a new blank project using
the example config file.

## Steps
Steps are single transformative operations that take place on a directory of
files. Examples of steps include 'import', 'export', 'compress', and 'chmod'.

The directory of files that the step performs operations on is called its
'workspace'. When run, each step has its own isolated workspace directory
as temporary folders created in the OS recommended area for temporary files.
Files can be copied from step to step using the `keep` field of a step. It
defaults to `**`, so will keep every file from the previous step if not 
specified.

A step looks a lot like this:
```yaml
step: export
keep: "game-{{ build_number }}.zip"
filter:
  options: [a_tag]
  targets: [StandaloneWindows]
using:
  backend: local
  container: C:/builds
  path_prefix: "{{ build_def.target }}"
```

Each step has to have the following fields:
- `step`: The type of step to use.
- `keep` (optional): A glob pattern of which files to keep from the previous step.
- `filter` (optional): Lets you filter on certain factors.
- `using`: What config values to provide to the step. Allows for customisable behaviour.

Some values given to a step are templated. This is useful as sometimes you want
build artifacts to be named based on the target or version number of the build.
In the example above, the build number is used in the `keep` field by templating
it like this: `game-{{ build_number }}.zip`. When rendered, this template would
simply insert the build number there, like: `game-0.1.1234.56789.zip`. Please
note that templated strings need to be wrapped in quotes due to the YAML format.

Additionally, environment variables are respected in fields that are able to
be templated. So you could insert the environment variable `$SOME_VARIABLE`
by simply specifying it like that as the value in the step config.

Filters can be applied to only run steps under certain conditions. The following
filters are available:
- `targets`: Only run this step for this set of build targets.
- `options`: Only run this step if this option is specified via the CLI (as `-o, --option`).

### Import
Imports files from an external directory to the step workspace. Supports
local store and cloud storage (at the moment just S3).

#### Example
```yaml
step: import
using:
  backend: s3
  region: fra1
  endpoint: https://fra1.digitaloceanspaces.com/
  container: $BUCKET_NAME
  key: "{{ build_def.target }}/game-{{ build_number }}.zip"
```

### Export
Like import, but instead copies files from the step workspace to an external
directory.

#### Example
```yaml
step: export
keep: "game-{{ build_number }}.zip"
filter:
  options: [upload]
using:
  backend: s3
  region: fra1
  endpoint: https://fra1.digitaloceanspaces.com/
  container: $BUCKET_NAME
  path_prefix: "{{ build_def.target }}"
```

### Compress
Compress the workspace into an archive file.

#### Example
```yaml
step: compress
using:
  format: zip
  archive_name: "game-{{ build_number }}"
```

This would produce an archive called `game-0.1.123.56789.zip`. This file
could then be used in the next step by adding this to the step:
```yaml
keep: "game-{{ build_number }}.zip"
```

The workspace for that step would then only contain the compressed archive
from the prior step.

### Chmod
Change permission bits of a file in the workspace.

#### Example
```yaml
step: chmod
using:
  file_name: {{ build_def.executable_name }}
  permissions: [S_IEXEC]
```

This step would ensure the executable from the build had the executable flag
set in the filesystem. Valid values for `permissions` are listed [here](https://docs.python.org/3/library/os.html#os.chmod).

### Butler
Run [itch.io Butler](https://itch.io/docs/butler/) push on a workspace. 
Requires Butler to be installed. This is mainly used for released as opposed
to builds.

#### Example
```yaml
step: butler
filter:
  targets: [StandaloneWindows]
using:
  directory: "coolgame-{{ build_number }}.zip"
  user: my-itchio-user
  game: coolgame
  channel: windows
  user_version: "{{ build_number }}"
```
This example would push `StandaloneWindows` target build archives to the
`windows` channel of the itch.io project.

## Builds, and post-build steps
```
$ toriicli build
```
Builds are defined as `build_defs` in the project config file. A build
definition has 2 things:
- `target`: The platform this build is for, from: https://docs.unity3d.com/ScriptReference/BuildTarget.html
- `executable_name`: The name of the executable. I.e. `"LSDR.exe"` for `"StandaloneWindows"`,
  or `"LSDR.app"` for `"StandaloneOSX"`.

When `toriicli build` is run in the project directory, the build defs are used
to generate a JSON file that's placed in the Unity project directory, and
Unity is executed with the `unity_build_execute_method` defined in the project
config. This is a static C# method that runs when Unity is launched. It
loads the generated build defs file, and builds the game for each platform in
a folder (configured by `build_output_folder`).

When Unity exits successfully, `toriicli` attempts to collect information from 
the builds based on the build defs it was given. It gets the path to each build 
as well as a version number from its assembly.

The build info for each build is then submitted to the build post-steps, where
files from the build are transformed in a number of steps before reaching
their intended destination (be it a folder, or some cloud storage somewhere).

Once the post steps have run, the builds are removed from the build output
folder, and the generated build defs JSON file is also deleted. This behaviour
can be toggled by providing the `--no-clean` option to `build`.

Build post-steps are specified in the `build_post_steps` area of the project
config file. They are run for every build def specified after the Unity build
completes.

Build post-steps have an implicit (unspecified) `import` step as the first
step. This step imports from the build output directory into a step workspace.
It's the exact same as specifying this as the first step (don't do this!):
```yaml
step: import
using:
  backend: local
  container: "{{ path }}"
```

### Example: compressing, storing, and optionally uploading to cloud storage
```yaml
build_post_steps:
  - step: compress
    using:
      format: zip
      archive_name: "game-{{ build_number }}"
  - step: export
    keep: "game-{{ build_number }}.zip"
    using:
      backend: local
      container: C:/game-builds
      path_prefix: "{{ build_def.target }}"
  - step: export
    keep: "game-{{ build_number }}.zip"
    filter:
      options: [upload]
    using:
      backend: s3
      region: fra1
      endpoint: https://fra1.digitaloceanspaces.com/
      container: $BUCKET_NAME
      path_prefix: "{{ build_def.target }}"
```

This example will compress the build files into a zip, copy the zip to
`C:/game-builds/{target-name}/game-{build_number}.zip`, and upload
to S3 cloud storage if the build command is run with the upload option (like
this: `toriicli build --option upload`).

## Releasing, and release steps
```
$ toriicli release 0.1.123.4567
```
So you've built the game and uploaded it somewhere - what happens when you
want to release it? Well you can use the `release` command for that.

You run it with a build number and it will run steps specified in the
`release_steps` section of the project config.

The `release` command supports `-o, --option` for step filtering in the same
way as build post-steps.

### Example: releasing from cloud storage with itch.io butler
```yaml
release_steps:
  - step: import
    using:
      backend: s3
      region: fra1
      endpoint: https://fra1.digitaloceanspaces.com/
      container: $BUCKET_NAME
      key: "{{ build_def.target }}/game-{{ build_number }}.zip"
  - step: butler
    filter:
      targets: [StandaloneWindows]
    using:
      directory: "game-{{ build_number }}.zip"
      user: my-itchio-user
      game: gamename
      channel: windows
      user_version: "{{ build_number }}"
```

Say you had just built and uploaded to cloud storage version `0.1.123.4567` of
your game (zipped). If you ran `toriicli release 0.1.123.4567` with the steps 
above, it would download that version of the archive from cloud storage
(see the `key` field of the import step), and then run butler using the zip
to release it. Pretty nifty.

## NuGet
Toriicli has the `nuget` subcommand for working with project NuGet packages.
To use this subcommand, you need the [NuGet CLI](https://docs.microsoft.com/en-us/nuget/reference/nuget-exe-cli-reference)
and a version of MSBuild. MSBuild comes with Visual Studio, but you can use 
[JetBrains MSBuild](https://blog.jetbrains.com/dotnet/2018/04/13/introducing-jetbrains-redistributable-msbuild/) 
or [Mono MSBuild](https://github.com/mono/msbuild) if you don't want to install Visual Studio.

**Note:** in order to function correctly, NuGet must be configured to install packages
into the `nuget-packages` directory in your Unity project folder. If you created
your Torii project with `toriicli new` then you don't need to worry about this.
If you are adapting an existing project to use `toriicli`, then make a file called
`nuget.config` in your Unity project folder, and put this text in it:
```xml
<configuration>
  <config>
    <add key="repositoryPath" value="nuget-packages" />
  </config>
</configuration>
```
This will ensure all NuGet packages get installed to the `nuget-packages` folder.

The reason for this is that Unity installs its own packages to the `packages` folder,
which NuGet is configured by default to use. They cannot both share the same space,
so we need to install NuGet packages to a separate place, as Unity is a bad roommate.

You'll also need a blank `packages.config` file, like this:
```xml
<?xml version="1.0" encoding="utf-8"?>
<packages>
</packages>
```

**Also note:** it's best to run these NuGet commands when Unity is not running,
as sometimes it will access the installed packages causing permissions errors.


### Installing a package
To install a package, simply run:

```bash
$ toriicli nuget install <package>
```

You can optionally specify a version too:
```bash
$ toriicli nuget install <package> --version 0.1.2
```

This will use NuGet to install the package to the `nuget-packages` folder, it will
add the package to your `packages.config` file, and it will copy the installed
package into your Unity project. By default it will copy it into the
`Assets/NuGetPackages` folder, but this can be configured by setting
`nuget_package_install_path` in the config.

Additionally, by default it will install the package for the latest version of
the .NET Framework it can, with a maximum version of .NET Framework 4.6.2.
This is because as far as I could see, this is the latest possible version
Unity supports. If you'd like to customise this, you can configure this by
setting `unity_dotnet_framework_version` in the config.

### Uninstalling a package
To uninstall a package, run:
```bash
$ toriicli nuget uninstall <package>
```

This will remove it from your Unity project, and your `packages.config`.

### Restoring packages
To sync your installed packages with your `packages.config` file, run:
```bash
$ toriicli nuget restore
```

This will reinstall all packages listed in `packages.config`. This is useful
when cloning a repo from fresh, as packages won't normally be committed to
the remote.