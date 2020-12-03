# Version metrics

## What is metric tracking?

MLflow defines a metric as "a (key, value) pair, where the value is numeric". Each metric can be updated throughout the course of the run (for example, to track how your model’s loss function is converging), and MLflow records and lets you visualize the metric’s full history".

## How to version metrics in a kedro project?

`kedro-mlflow` introduces a new ``AbstractDataSet`` called ``MlflowMetricsDataSet``. It is a wrapper around a dictionary with metrics which is returned by node and log metrics in MLflow.

Since it is an ``AbstractDataSet``, it can be used with the YAML API. You can define it as:

```yaml
my_model_metrics:
    type: kedro_mlflow.io.metrics.MlflowMetricsDataSet
```

You can provide a prefix key, which is useful in situations like when you have multiple nodes producing metrics with the same names which you want to distinguish. If you are using the ``MlflowPipelineHook``, it will handle that automatically for you by giving as prefix metrics data set name. In the example above the prefix would be ``my_model_metrics``.

Let's look at an example with custom prefix:

```yaml
my_model_metrics:
    type: kedro_mlflow.io.metrics.MlflowMetricsDataSet
    prefix: foo
```

## How to return metrics from a node?

Let assume that you have node which doesn't have any inputs and returns dictionary with metrics to log:

```python
def metrics_node() -> Dict[str, Union[float, List[float]]]:
    return {
        "metric1": {"value": 1.1, "step": 1},
        "metric2": [{"value": 1.1, "step": 1}, {"value": 1.2, "step": 2}]
    }
```

As you can see above, ``kedro_mlflow.io.metrics.MlflowMetricsDataSet`` can take metrics as:

- ``Dict[str, key]``
- ``List[Dict[str, key]]``

To store metrics we need to define metrics dataset in Kedro Catalog:

```yaml
my_model_metrics:
    type: kedro_mlflow.io.metrics.MlflowMetricsDataSet
```

Within a kedro run, the ``MlflowPipelineHook`` will automatically prefix the metrics datasets with their name in the catalog. In our example, the metrics will be stored in Mlflow with the following keys: ``my_model_metrics.metric1``, ``my_model_metrics.metric2``.

It is also prossible to provide a prefix manually:

```yaml
my_model_metrics:
    type: kedro_mlflow.io.metrics.MlflowMetricsDataSet
    prefix: foo
```

which would result in metrics logged as ``foo.metric1`` and ``foo.metric2``.

As any entry in the catalog, the metrics data set must be defined in a Kedro pipeline:

```python
def create_pipeline() -> Pipeline:
    return Pipeline(node(
        func=metrics_node,
        inputs=None,
        outputs="my_model_metrics",
        name="log_metrics",
    ))
```
