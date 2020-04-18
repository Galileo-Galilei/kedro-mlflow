# Introduction
``kedro-mlflow`` is a [kedro-plugin](https://kedro.readthedocs.io/en/stable/04_user_guide/10_developing_plugins.html) for integration of [mlflow](https://mlflow.org/docs/latest/index.html) capabilities inside [kedro](https://kedro.readthedocs.io/en/stable/index.html) projects. Its core functionalities are :
- **versioning**: you can effortlessly register your parameters or your datasets with minimal configuration in a kedro run. Later, you will be able to browse your runs in the mlflow UI, and retrieve the runs you want. This is directly linked to [Mlflow Tracking](https://www.mlflow.org/docs/latest/tracking.html)
- **model packaging**: ``kedro-mlflow`` offers a convenient API to register a pipeline as a ``model`` in the mlflow sense. Consequently, you can *API-fy* your kedro pipeline with one line of code, or share a model with without worrying of the preprocessing to be made for further use. This is directly linked to [Mlflow Models](https://www.mlflow.org/docs/latest/models.html)

# Release history
The release history is available [here](CHANGELOG.md).

**Coming soon:**
- enhanced documentation, especially with detailed tutorials for ``PipelineML`` class and advanced versioning parametrisation
- better integration to [Mlflow Projects](https://www.mlflow.org/docs/latest/projects.html) 
- better integration to [Mlflow Model Registry](https://www.mlflow.org/docs/latest/model-registry.html) 
- better CLI experience and bug fixes
- ability to retrieve parameters / re-run a former run for reproducibility / collaboration

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
Type  ``kedro info`` in a terminal to check the installation. If it has succeeded, you should see the following ascii art:
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

## A "hello world" example
### Step 1 : Create a kedro project
If you do not have a kedro project yet, you can create it with ``kedro new`` command. [See the kedro docs for a tutorial](https://kedro.readthedocs.io/en/latest/02_getting_started/03_new_project.html).

For this tutorial and if you do not have a real-world project, I strongly suggest that you accept to include the proposed example to make a demo of this plugin out of the box. 

### Step 2 : update the template
Position yourself with at the root (i.e. the folder with the ``.kedro.yml`` file)
```
$ cd path/to/your/project
```
Run the init command : 
```
$ kedro mlflow init
```
*Note : If the warning ``"You have not updated your template yet. This is mandatory to use 'kedro-mlflow' plugin. Please run the following command before you can access to other commands : '$ kedro mlflow init'`` is raised, this is a bug to be corrected and you can safely ignore it.*
- If you have never modified your ``run.py`` manually, it should run smoothly.
- If you have modified you ``run.py`` manually since the creation of the project, you must [set up the hooks manually](#new-hooks) or use :
```
$ kedro mlflow init --force
```
to override your ``run.py`` (be cautious if you do this in an existing project !).

### Run the project
You can now run 
```
$ kedro run
```
### Open and check what is logged
Run the following command :
```
$ kedro mlflow ui
``` 
and opens your browser to [http://localhost:5000](http://localhost:5000). You will reach the mlflow ui. 

Click on your project name, and then last run recorded, and enjoy what is logged!

### Going further
- You want to log additional metrics to the run? -> [See ``mlflow.log_metric`` and add it to your functions](https://www.mlflow.org/docs/latest/python_api/mlflow.html#mlflow.log_metric) !
- You want to log nice dataviz of your pipeline that you register with ``MatplotlibWriter``? -> [Try ``MlflowDataSet`` to log any local files (.png, .pkl, .csv...) *automagically*](#new-dataset)!
- You want to create easily an API to share your awesome model to anyone? -> [See if ``pipeline_ml`` can fit your needs](#new-pipeline)
- You want to do something that is not straigthforward with current implementation? Open an issue, and let's see what happens! 
# Tutorial
TO BE DONE... It will contain [more explanations and examples of the ``pipeline_ml`` function](#new-pipeline).

# Plugin overview
The current version of ``kedro-mlflow`` provides the following items:
### New ``cli`` commands:
1. ``kedro mlflow init``: this command is needed to initalize your project. You cannot run any other commands before you run this one once. It performs 2 actions:
    - creates a ``mlflow.yml`` configuration file in your ``conf/base`` folder
    - replace the ``src/PYTHON_PACKAGE/run.py`` file by an updated version of the template. If your template has been modified since project creation, a warning wil be raised. You can either run ``kedro mlflow init --force`` to ignore this warning (but this will erase your ``run.py``) or [set hooks manually](#new-hooks).
2. ``kedro mlflow ui``: this command opens the mlflow UI (basically launches the ``mlflow ui`` command with the configuration of your ``mlflow.yml`` file)
### New ``DataSet``:
``MlflowDataSet`` is a wrapper for any ``AbstractDataSet`` which logs the dataset automatically in mlflow as an artifact when its ``save`` method is called. It can be used both with the YAML API:
```
my_dataset_to_version:
    type: kedro_mlflow.io.MlflowDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
```
or with additional parameters:
```
my_dataset_to_version:
    type: kedro_mlflow.io.MlflowDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
        load_args:
            sep: ;
        save_args:
            sep: ;
        # ... any other valid arguments for data_set
    run_id: 13245678910111213  # a valid mlflow run to log in. If None, default to active run
    artifact_path: reporting  # relative path where the artifact must be stored. if None, saved in root folder.
```
or with the python API:
```
from kedro_mlflow.io import MlflowDataSet
from kedro.extras.datasets.pandas import CSVDataSet
csv_dataset = MlflowDataSet(data_set={"type": CSVDataSet, 
                                      "filepath": r"/path/to/a/local/destination/file.csv"})
csv_dataset.save(data=pd.DataFrame({"a":[1,2], "b": [3,4]}))
```

### New ``Hooks``
This package provides 2 new hooks:
1. The ``MlflowPipelineHook`` :
    1.  manages mlflow settings at the beginning and the end of the run (run start / end). 
    2. log useful informations for reproducibility as ``mlflow tags`` (including kedro ``Journal`` information and the commands used to launch the run.)
    3. register the pipeline as a valid ``mlflow model`` if [it is a ``PipelineML`` instance](#new-pipeline)
1. The ``MlflowNodeHook`` :
    1. must be used with the ``MlflowPipelineHook``
    2. autolog nodes parameters each time the pipeline is run (with ``kedro run`` or programatically).

**These hooks need to be registered in the the ``run.py`` file**. You can either :
- [register them manually](https://kedro.readthedocs.io/en/latest/04_user_guide/15_hooks.html#registering-your-hook-implementations-with-kedro). Your run.py should look like the following code snippet :
``` 
from kedro_mlflow.hooks import MlflowNodeHook, MlflowPipelineHook
from pk.pipeline import create_pipelines

class ProjectContext(KedroContext):
    """Users can override the remaining methods from the parent class here,
    or create new ones (e.g. as required by plugins)
    """

    project_name = "YOUR PROJECT NAME"
    project_version = "0.15.9"
    hooks = (
        MlflowNodeHook(flatten_dict_params=False),
        MlflowPipelineHook(model_name="YOUR_PYTHON_PACKAGE",
                           conda_env="src/requirements.txt")
    )
```
- (**RECOMMENDED**) [use the ``kedro mlflow init`` command](new-cli-commands).

### New ``Pipeline``
``PipelineML`` is a new class which extends ``Pipeline`` and enable to bind two pipelines (one of training, one of inference) together. This class comes with a ``KedroPipelineModel`` class for logging it in mlflow. A pipeline logged as a mlflow model can be served using ``mlflow models serve`` and ``mlflow models predict`` command.  

The ``PipelineML`` class is not intended to be used directly. A ``pipeline_ml`` factory is provided for user friendly interface. 

Example within kedro template:
```
# in src/PYTHON_PACKAGE/pipeline.py

from PYTHON_PACKAGE.pipelines import data_science as ds

def create_pipelines(**kwargs) -> Dict[str, Pipeline]:
    data_science_pipeline = ds.create_pipeline()
    training_pipeline = pipeline_ml(training=data_science_pipeline.only_nodes_with_tags("training"), # or whatever your logic is for filtering
                                    inference=data_science_pipeline.only_nodes_with_tags("inference"))

    return {
        "ds": data_science_pipeline,
        "training": training_pipeline, 
        "__default__": data_engineering_pipeline + data_science_pipeline,
    }

```
Now each time you will run ``kedro run --pipeline=training`` (provided you registered ``MlflowPipelineHook`` in you ``run.py``), the full inference pipeline will be registered as a mlflow model (with all the outputs produced by training as artifacts : the machine learning, but also the *scaler*, *vectorizer*, *imputer*, or whatever object fitted on data you create in ``training`` and that is used in ``inference``).

*Note: If you want to log a ``PipelineML`` object in ``mlflow`` programatically, you can use the following code snippet:* 
```
from pathlib import Path
from kedro.context import load_context
from kedro_mlflow.mlflow import KedroPipelineModel

# pipeline_training is your PipelineML object, created as previsously
catalog = load_context(".").io

# artifacts are all the inputs of the inference pipelines that are persisted in the catalog
pipeline_catalog = pipeline_training.extract_pipeline_catalog(catalog) 
artifacts = {name: Path(dataset._filepath).resolve().as_uri()
                for name, dataset in pipeline_catalog._data_sets.items()
                if name != pipeline_training.model_input_name}


mlflow.pyfunc.log_model(artifact_path="model",
                        python_model=KedroPipelineModel(pipeline_ml=pipeline_training,
                                                        catalog=pipeline_catalog),
                        artifacts=artifacts,
                            conda_env={"python": "3.7.0"})
```



