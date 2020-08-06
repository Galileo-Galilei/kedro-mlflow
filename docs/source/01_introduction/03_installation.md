# Installation
## Pre-requisites
I strongly recommend to use ``conda`` (a package manager) to create an environment in order to avoid version conflicts between packages.

I also recommend to read [Kedro installation guide](https://kedro.readthedocs.io/en/stable/02_getting_started/01_prerequisites.html) to set up your Kedro project.

## Installation guide
The plugin is compatible with ``kedro>=0.16.0``. Since Kedro tries to enforce backward compatibility, it will very likely remain compatible with further versions.

First, install Kedro from PyPI and ensure you have a ``0.16.0`` version:
```console
pip install --upgrade "kedro>=0.16.0,<0.17.0"
```

Second, install ``kedro-mlflow`` plugin from ``PyPi``:
```console
pip install --upgrade kedro-mlflow
```

You may want to install the develop branch which has unreleased features:
```console
pip install git+https://github.com/Galileo-Galilei/kedro-mlflow.git@develop
```
## Check the installation
Type  ``kedro info`` in a terminal to check the installation. If it has succeeded, you should see the following ascii art:
```console
 _            _
| | _____  __| |_ __ ___
| |/ / _ \/ _` | '__/ _ \
|   <  __/ (_| | | | (_) |
|_|\_\___|\__,_|_|  \___/
v0.16.2

kedro allows teams to create analytics
projects. It is developed as part of
the Kedro initiative at QuantumBlack.

Installed plugins:
kedro_mlflow: 0.2.0 (hooks:global,project)
```
The version ``0.2.0`` of the plugin is installed and has both global and project commands.

That's it! You are now ready to go!

## Available commands
With the ``kedro mlflow -h`` command outside of a kedro project, you now see the following output:

```console
Usage: kedro mlflow [OPTIONS] COMMAND [ARGS]...

  Use mlflow-specific commands inside kedro project.

Options:
  -h, --help  Show this message and exit.

Commands:
  new  Create a new kedro project with updated template.
```
