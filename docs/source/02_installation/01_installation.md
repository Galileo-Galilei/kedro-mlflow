# Installation guide

## Pre-requisites

### Create a virtual environment

I strongly recommend to use ``conda`` (a package manager) to create an environment in order to avoid version conflicts between packages.

I also recommend to read [Kedro installation guide](https://kedro.readthedocs.io/en/latest/get_started/install.html) to set up your Kedro project.

```console
conda create -n <your-environment-name> python=<3.[6-8].X>
```

For the rest of the section, we assume the envirpnment is activated:

```console
conda activate <your-environment-name>
```

### Check your kedro version

If you have an existing environment with kedro already installed, make sure its version is above `0.16.0`. `kedro-mlflow` cannot be used with `kedro<0.16.0`, and if you install it in an existing environment, it will reinstall a more up-to-date version of kedro and likely mess your project up until you reinstall the proper version of kedro (the one you originally created the project with).

```console
pip show kedro
```

should return:

```console
Name: kedro
Version: <your-kedro-version>  # <-- make sure it is above 0.16.0, <0.17.0
Summary: Kedro helps you build production-ready data and analytics pipelines
Home-page: https://github.com/quantumblacklabs/kedro
Author: QuantumBlack Labs
Author-email: None
License: Apache Software License (Apache 2.0)
Location: <...>\anaconda3\envs\<your-environment-name>\lib\site-packages
Requires: pip-tools, cachetools, fsspec, toposort, anyconfig, PyYAML, click, pluggy, jmespath, python-json-logger, jupyter-client, setuptools, cookiecutter
```

## Install the plugin

The current version of the plugin is compatible with ``kedro>=0.16.0``. Since Kedro tries to enforce backward compatibility, it will very likely remain compatible with further versions.

### Install from PyPI

You can install ``kedro-mlflow`` plugin from ``PyPi`` with `pip`:

```console
pip install --upgrade kedro-mlflow
```

### Install from sources

You may want to install the master branch which has unreleased features:

```console
pip install git+https://github.com/Galileo-Galilei/kedro-mlflow.git
```

## Check the installation

Type  ``kedro info`` in a terminal to check the installation. If it has succeeded, you should see the following ascii art:

```console
 _            _
| | _____  __| |_ __ ___
| |/ / _ \/ _` | '__/ _ \
|   <  __/ (_| | | | (_) |
|_|\_\___|\__,_|_|  \___/
v0.16.<x>

kedro allows teams to create analytics
projects. It is developed as part of
the Kedro initiative at QuantumBlack.

Installed plugins:
kedro_mlflow: 0.11.7 (hooks:global,project)
```

The version ``0.11.7`` of the plugin is installed and has both global and project commands.

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

*Note: For now, the `kedro mlflow new` command is not implemented. You must use `kedro new` to create a project, and then call `kedro mlflow init` inside this new project.*
