# Installation guide

## Pre-requisites

### Create a virtual environment

I strongly recommend to create a virtual environment in order to avoid version conflicts between packages. I use ``conda`` in this tutorial.

I also recommend to read [Kedro installation guide](https://kedro.readthedocs.io/en/latest/get_started/install.html) to set up your Kedro project.

```console
conda create -n <your-environment-name> python=<3.[6-8].X>
```

For the rest of the section, we assume the environment is activated:

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

There are versions of the plugin compatible up to ``kedro>=0.16.0`` and ``mlflow>=0.8.0``. ``kedro-mlflow`` stops adding features to a minor version 2 to 6 months after a new kedro release.

::::{tab-set}

:::{tab-item} Install with pip / uv

You can install ``kedro-mlflow`` plugin from ``PyPi`` with `pip`:

```console
pip install --upgrade kedro-mlflow
```

If you prefer uv and have it installed, you can use:

```console
uv pip install --upgrade kedro-mlflow
```


:::

:::{tab-item} Install with conda / mamba / micromamba

You can install ``kedro-mlflow`` plugin with `conda` from the ``conda-forge`` channel:

```console
conda install kedro-mlflow -c conda-forge
```

:::

:::{tab-item} Install from github

You may want to install the master branch from source which has unreleased features:

```console
pip install git+https://github.com/Galileo-Galilei/kedro-mlflow.git
```

:::

::::


## Check the installation

Enter  ``kedro info`` in a terminal with the activated virtual env to check the installation. If it has succeeded, you should see the following ascii art:

```console
 _            _
| | _____  __| |_ __ ___
| |/ / _ \/ _` | '__/ _ \
|   <  __/ (_| | | | (_) |
|_|\_\___|\__,_|_|  \___/
v0.<minor>.<patch>

kedro allows teams to create analytics
projects. It is developed as part of
the Kedro initiative at QuantumBlack.

Installed plugins:
kedro_mlflow: 0.14.0 (hooks:global,project)
```

The version ``0.14.0`` of the plugin is installed and has both global and project commands.

That's it! You are now ready to go!

## Available commands

With the ``kedro mlflow -h`` command outside of a kedro project, you now see the following output:

```console
Usage: kedro mlflow [OPTIONS] COMMAND [ARGS]...

  Use mlflow-specific commands inside kedro project.

Options:
  -h, --help  Show this message and exit.
```
