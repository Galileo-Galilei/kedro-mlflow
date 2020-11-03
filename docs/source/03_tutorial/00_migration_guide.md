# Migration guide

This page explains how to migrate between versions with breaking changes, if you had an existing kedro project.

## Migration from 0.3.0 to 0.4.0

### Catalog entries

Replace the follwoing entries:

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

Be aware that if you had trained saved a pipeline as a mlflow model with `pipeline_ml_factory`, retraining this pipeline with `kedro-mlflow==0.4.0` will lead to a new behaviour. Let assume the name of your output in the `DataCatalog` was `predictions`, the output of a registered model will be modified from:

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
