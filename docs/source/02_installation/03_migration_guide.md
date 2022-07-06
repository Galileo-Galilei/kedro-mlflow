# Migration guide

This page explains how to migrate an existing kedro project to a more up to date `kedro-mlflow` versions with breaking changes.

## Migration from 0.10.x to 0.11.x

1. If you are registering your ``kedro_mlflow`` hooks manually (instead of using automatic registeringfrom plugin, which is the default), change your ``settings.py``

from this

```python
# <your_project>/src/<your_project>/settings.py
from kedro_mlflow.framework.hooks import MlflowHook

HOOKS = (MlflowPipelineHook(), MlflowNodeHook)
```

to this:
```python
# <your_project>/src/<your_project>/settings.py
from kedro_mlflow.framework.hooks import MlflowHook

HOOKS = (MlflowHook,)
```

2. The `get_mlflow_config` public method has been removed and the mlflow configuration is now automatically stored in the ``mlflow`` attribute of ``KedroContext``. if you need to access the mlflow configuration, you can use:

```python
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

bootstrap_project(project_path)
with KedroSession.create(
    project_path=project_path,
) as session:
    context = session.load_context()
    print(context.mlflow)  # this is where mlflow configuration is stored
```

3. Remove the ``server.stores_environment_variables`` key from ``mlflow.yml``. This is a dead key which was unused. It will now throw an error if it is still written in ``mlflow.yml``.  

## Migration from 0.9.x to 0.10.x

You must upgrade your kedro version to ``kedro==0.18.1`` to use ``kedro_mlflow>=0.10``.

## Migration from 0.8.x to 0.9.x

There are no breaking change in this patch release except if you retrieve the mlflow configuration manually (e.g. in a script or a jupyter notebok). The ``setup()`` method needs to be called with ``context``:

```python
from kedro.framework.context import load_context
from kedro_mlflow.config import get_mlflow_config

context = load_context(".")

# the new best practice is just to remove these lines
mlflow_config = get_mlflow_config(context)  # pass context instead of session
mlflow_config.setup(context)  # pass context instead of session
```

This is not necessary: the mlflow config is automatically set up when the context is loaded, so unless you need to access the config manually you can get rid of these 2 lines

## Migration from 0.7.x to 0.8.x

- Update the ``mlflow.yml`` configuration file with ``kedro mlflow init --force`` command
- `pipeline_ml_factory(pipeline_ml=<your-pipeline-ml>,...)` (resp. `KedroPipelineModel(pipeline_ml=<your-pipeline-ml>, ...)`) first argument is renamed `pipeline`. Change the call to `pipeline_ml_factory(pipeline=<your-pipeline-ml>)` (resp. `KedroPipelineModel(pipeline=<your-pipeline-ml>, ...)`).
- Change the call from `pipeline_ml_factory(..., model_signature=<model-signature>, conda_env=<conda-env>, model_name=<model_name>)` to `` pipeline_ml_factory(..., log_model_kwargs=dict(signature=<model-signature>, conda_env=<conda-env>, artifact_path=<model_name>})`. Notice that the arguments are renamed to match mlflow's and they are passed as a dict in `log_model_kwargs`.


## Migration from 0.6.x to 0.7.x

If you are working with ``kedro==0.17.0``, update your template to ``kedro>=0.17.1``.

## Migration from 0.5.x to 0.6.x

``kedro==0.16.x`` is no longer supported. You need to update your project template to ``kedro==0.17.0`` template.

## Migration from 0.4.x to 0.5.x

The only breaking change with the previous release is the format of ``KedroPipelineMLModel`` class. Hence, if you saved a pipeline as a Mlflow Model with `pipeline_ml_factory` in ``kedro-mlflow==0.4.x``, loading it (either with ``MlflowModelLoggerDataSet`` or ``mlflow.pyfunc.load_model``) with ``kedro-mlflow==0.5.0`` installed will raise an error. You will need either to retrain the model or to load it with ``kedro-mlflow==0.4.x``.

## Migration from 0.4.0 to 0.4.1

There are no breaking change in this patch release except if you retrieve the mlflow configuration manually (e.g. in a script or a jupyter notebok). You must add an extra call to the ``setup()`` method:

```python
from kedro.framework.context import load_context
from kedro_mlflow.config import get_mlflow_config

context = load_context(".")
mlflow_config = get_mlflow_config(context)
mlflow_config.setup()  # <-- add this line which did not exists in 0.4.0
```

## Migration from 0.3.x to 0.4.x

### Catalog entries

Replace the following entries:

| old                                     | new                                               |
| :-------------------------------------- | :------------------------------------------------ |
| `kedro_mlflow.io.MlflowArtifactDataSet` | `kedro_mlflow.io.artifacts.MlflowArtifactDataSet` |
| `kedro_mlflow.io.MlflowMetricsDataSet`  | `kedro_mlflow.io.metrics.MlflowMetricsDataSet`    |

### Hooks

Hooks are now auto-registered if you use `kedro>=0.16.4`. You can remove the following entry from your `run.py`:

```python
hooks = (MlflowPipelineHook(), MlflowNodeHook())
```

### KedroPipelineModel

Be aware that if you have saved a pipeline as a mlflow model with `pipeline_ml_factory`, retraining this pipeline with `kedro-mlflow==0.4.0` will lead to a new behaviour. Let assume the name of your output in the `DataCatalog` was `predictions`, the output of a registered model will be modified from:

```json
{
    predictions:
        {
            <your model-predictions>
        }
}
```

to:

```json
{
    <your model-predictions>
}
```

Thus, parsing the predictions of this model must be updated accordingly.
