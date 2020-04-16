# Introduction
``kedro-mlflow`` is a [kedro-plugin](https://kedro.readthedocs.io/en/stable/04_user_guide/10_developing_plugins.html) for integration of [mlflow](https://mlflow.org/docs/latest/index.html) capabilities inside [kedro](https://kedro.readthedocs.io/en/stable/index.html) projects. Its core functionalities are :
- **versioning**: you can effortlessly register your parameters or your datasets with minimal configuration in a kedro run. Later, you will be able to browse your runs in the mlflow UI, and retrieve the runs you want.
- **model packaging**: ``kedro-mlflow`` offers a convenient API to register a pipeline as a ``model`` in the mlflow sense. Consequently, you can *API-fy* your kedro pipeline with one line of code, or share a model with without worrying of the preprocessing to be made for further use.  

# Release history
The release history is available [here](CHANGELOG.MD).

# Getting started

## Installation 
### Pre-requisites
I strongly recommend to use ``conda`` (a package manager) to create an environment in order to avoid version conflicts between packages. This is specially important because **this package uses the ``develop`` version of kedro** which is very likely not the default one you use in your projects.

I also recommend to read [``kedro`` installation guide](https://kedro.readthedocs.io/en/stable/02_getting_started/01_prerequisites.html).

### Installation guide
First, install the ``develop`` version of kedro from github  which is the only compatible with current kedro-mlflow version:
```
pip install --upgrade git+https://github.com/quantumblacklabs/kedro.git@develop
```
Second, and since the package is not on ``PyPi`` yet, you must install it from sources:
```
pip install  git+https://github.com/Galileo-Galilei/kedro-mlflow.git
```
**Note :** with this develop version of kedro, you need to install [extras dependencies by hand](https://kedro.readthedocs.io/en/latest/02_getting_started/02_install.html#optional-dependencies). You will very likely need :

```
pip install kedro[pandas]
```
else check the documentation and install the dependencies you need.
### Check the installation
Type  ``kedro info`` in a command line to check the installation. If it has succeeded, you should see the following ascii art:
```
 _            _
| | _____  __| |_ __ ___
| |/ / _ \/ _` | '__/ _ \
|   <  __/ (_| | | | (_) |
|_|\_\___|\__,_|_|  \___/
v0.15.9

kedro allows teams to create analytics
projects. It is developed as part of
the Kedro initiative at QuantumBlack.

Installed plugins:
kedro_mlflow: 0.1.0 (hooks:global,project)
```
The version 0.1.0 of the plugin is installed ans has both global and project commands.

That's it! You are now ready to go!

## Overview
The current version of ``kedro-mlflow`` provides the following items:
### New ``cli`` commands:
1. ``kedro mlflow template``: this command is needed to initalize your project. You cannot run any other commands before you run this one once. It performs 2 actions:
    - creates a ``mlflow.yml`` configuration file in your ``conf/base`` folder
    - replace the ``src/PYTHON_PACKAGE/run.py`` file by an updated version of the template. If your template has been modified since project creation, a warning wil be raised.
2. ``kedro mlflow ui``: this command opens the mlflow UI (basically launches the ``mlflow ui`` command with the configuration of your ``mlflow.yml`` file)
### New ``DataSet``:
``MlflowDataSet`` is a wrapper for any ``AbstractDataSet`` wich logs the dataset automatically in mlflow as an artifact when its ``save`` method is called. It can be used both with the
YAML API:
```
my_dataset_to_version:
    type: kedro_mlflow.io.MlflowDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
```
or with additional details:
```
my_dataset_to_version:
    type: kedro_mlflow.io.MlflowDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
        load_args:
            ...
        save_args:
            ...
        ...
    run_id: 13245678910111213  # a valid mlflow run to log in. If None, default to active run
    artifact_path: reporting  # relative path where the artifact must be stored. if None, saved in root folder
```
or with the python API:
```
from kedro_mlflow.io import MlflowDataSet
from kedro.extras.datasets.pandas import CSVDataSet
csv_dataset = MlflowDataSet(data_set={"type": CSVDataSet, "filepath": r"/path/to/a/local/destination/file.csv")
```
### New ``Pipeline``
``PipelineML`` is a new class which inherits from 
# Tutorial