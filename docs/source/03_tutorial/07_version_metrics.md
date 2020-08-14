# Version metrics

## What is metric tracking?

Mlflow defines metrics as "Key-value metrics, where the value is numeric. Each metric can be updated throughout the course of the run (for example, to track how your model’s loss function is converging), and MLflow records and lets you visualize the metric’s full history".
## How to version metrics in a kedro project?

kedro-mlflow introduces a new ``AbstractDataSet`` called ``MlflowMetricsDataSet``. It is wrapper around dictionary with metrics which is returned by node, log metrics in MLflow and if filepath is specified saves data to file in ``json`` format.

Since it is a ``AbstractDataSet``, it can be used with the YAML API. You can define it as:

```yaml
my_model_metrics:
    type: kedro_mlflow.MlflowMetricsDataSet
    filepath: /path/to/a/destination/file.json
```

It can get also ``prefix`` configuration option. This is useful especially when your pipeline evaluate metrics on different datasets. For example:

```yaml
my_model_metrics_dev:
    type: kedro_mlflow.MlflowMetricsDataSet
    filepath: /path/to/a/destination/file.json
    prefix: dev
my_model_metrics_test:
    type: kedro_mlflow.MlflowMetricsDataSet
    filepath: /path/to/a/destination/file.json
    prefix: test
```

In that scenario metrics will be available in MLflow with given prefixes. For example your ``accuracy`` metric from example above, for ``my_model_metrics_test`` will be stored under key ``test.accuracy``, for ``my_model_metrics_dev``, under ker ``dev.accuracy``.

If you don't have need to store local copy you can omit filepath:

```yaml
my_model_metrics:
    type: kedro_mlflow.MlflowMetricsDataSet
```

In that case metrics will be logged just in MLflow. It's important to note that you will not be able to fetch this dataset using Kedro Catalog.


## How to return metrics from node?

Let assume that you have node which doesn't have any inputs and returns dictionary with metrics to log:

```python
def metrics_node() -> Dict[str, Union[float, List[float]]]:
    return {
        "metric1": 1.0,
        "metric2": [1.0, 1.1]
    }
```

As you can see above, ``kedro_mlflow.MlflowMetricsDataSet`` can take as metrics ``floats`` or ``lists`` of ``floats``. In first case under the given metric key just one value will be logged, in second a series of values.

To store metrics we need to define metrics dataset in Kedro Catalog:

```yaml
my_model_metrics:
    type: kedro_mlflow.MlflowMetricsDataSet
    filepath: /path/to/a/destination/file.json
```

To fulfill example we also need pipeline which will use this node and store metrics under ``my_model_metrics`` name.

```python
def create_pipeline() -> Pipeline:
    return Pipeline(node(
        func=metrics_node,
        inputs=None,
        outputs="my_model_metrics",
        name="log_metrics",
    ))
```
