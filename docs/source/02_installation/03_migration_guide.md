# Migration guide

This page explains how to migrate an existing kedro project to a more up to date `kedro-mlflow` versions with breaking changes.

## Migration from 0.5.0 to 0.6.0

``kedro==0.16.x`` is no longer supported. You need to update your project template to ``kedro==0.17.0`` template.

## Migration from 0.4.1 to 0.5.0

The only breaking change with the previous release is the format of ``KedroPipelineMLModel`` class. Hence, if you saved a pipeline as a Mlflow Model with `pipeline_ml_factory` in ``kedro-mlflow==0.4.x``, loading it (either with ``MlflowModelLoggerDataSet`` or ``mlflow.pyfunc.load_model``) with ``kedro-mlflow==0.5.0`` installed will raise an error. You will need either to retrain the model or to load it with ``kedro-mlflow==0.4.x``.

## Migration from 0.4.0 to 0.4.1

There are no breaking change in this patch release except if you retrieve the mlflow configuration manually (e.g. in a script or a jupyter notebok). You must add an extra call to the ``setup()`` method:

```python
from kedro.framework.context import load_context
from kedro_mlflow.framework.context import get_mlflow_config

context=load_context(".")
mlflow_config=get_mlflow_config(context)
mlflow_config.setup() # <-- add this line which did not exists in 0.4.0
```

## Migration from 0.3.0 to 0.4.0

### Catalog entries

Replace the following entries:

|old                                    |new                                              |
|:--------------------------------------|:------------------------------------------------|
|`kedro_mlflow.io.MlflowArtifactDataSet`|`kedro_mlflow.io.artifacts.MlflowArtifactDataSet`|
|`kedro_mlflow.io.MlflowMetricsDataSet` |`kedro_mlflow.io.metrics.MlflowMetricsDataSet`   |

### Hooks

Hooks are now auto-registered if you use `kedro>=0.16.4`. You can remove the following entry from your `run.py`:

```python
hooks = (
    MlflowPipelineHook(),
    MlflowNodeHook()
)
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
