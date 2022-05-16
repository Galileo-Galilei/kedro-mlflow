# Version metrics

## What is metric tracking?

MLflow defines a metric as "a (key, value) pair, where the value is numeric". Each metric can be updated throughout the course of the run (for example, to track how your model’s loss function is converging), and MLflow records and lets you visualize the metric’s full history".

## How to version metrics in a kedro project?

`kedro-mlflow` introduces 3 ``AbstractDataSet`` to manage metrics:
- ``MlflowMetricDataSet`` which can log a float as a metric
- ``MlflowMetricHistoryDataSet`` which can log the evolution over time of a given metric, e.g. a list or a dict of float.
- ``MlflowMetricsDataSet``. It is a wrapper around a dictionary with metrics which is returned by node and log metrics in MLflow.

### Saving a single float as a metric with ``MlflowMetricDataSet``

The ``MlflowMetricDataSet`` is an ``AbstractDataSet`` which enable to save or load a ``float`` as a mlflow metric. You must specify the ``key`` (i.e. the name to display in mlflow) when creating the dataset. Somes examples follow:

- The most basic usage is to create the dataset and save a a value:

```python
from kedro_mlflow.io.metrics import MlflowMetricDataSet

metric_ds = MlflowMetricDataSet(key="my_metric")
with mlflow.start_run():
    metric_ds.save(
        0.3
    )  # create a "my_metric=0.3" value in the "metric" field in mlflow UI
```

```{warning}
Unlike mlflow default behaviour, if there is no active run, no run is created.
```

- You can also specify a ``run_id`` instead of logging in the active run:

```python
from kedro_mlflow.io.metrics import MlflowMetricDataSet

metric_ds = MlflowMetricDataSet(key="my_metric", run_id="123456789")
with mlflow.start_run():
    metric_ds.save(
        0.3
    )  # create a "my_metric=0.3" value in the "metric" field of the run 123456789
```

It is also possible to pass ``load_args`` and ``save_args`` to control which step should be logged (in case you have logged several step for the same metric.) ``save_args`` accepts a ``mode`` key which can be set to ``overwrite`` (mlflow default) or ``append``. In append mode, if no step is specified, saving the metric will "bump" the last existing step to create a linear history. **This is very useful if you have a monitoring pipeline which calculates a metric frequently to check the performance of a deployed model.**

```python
from kedro_mlflow.io.metrics import MlflowMetricDataSet

metric_ds = MlflowMetricDataSet(
    key="my_metric", load_args={"step": 1}, save_args={"mode": "append"}
)

with mlflow.start_run():
    metric_ds.save(0)  # step 0 stored for "my_metric"
    metric_ds.save(0.1)  # step 1 stored for "my_metric"
    metric_ds.save(0.2)  # step 2 stored for "my_metric"

    my_metric = metric_ds.load()  # value=0.1 (step number 1)
```

Since it is an ``AbstractDataSet``, it can be used with the YAML API in your ``catalog.yml``, e.g. :

```yaml
my_model_metric:
    type: kedro_mlflow.io.metrics.MlflowMetricDataSet
    run_id: 123456 # OPTIONAL, you should likely let it empty to log in the current run
    key: my_awesome_name # OPTIONAL: if not provided, the dataset name will be sued (here "my_model_metric")
    load_args:
        step: ... # OPTIONAL: likely not provided, unless you have a very good reason to do so
    save_args:
        step: ... # OPTIONAL: likely not provided, unless you have a very good reason to do so
        mode: append #  OPTIONAL: likely better than the default "overwrite". Will be ignored if "step" is provided.
```

### Saving the evolution of a metric during training with ``MlflowMetricHistoryDataSet``

The ``MlflowMetricDataSet`` is an ``AbstractDataSet`` which enable to save or load the evolutionf of a metric with various formats. You must specify the ``key`` (i.e. the name to display in mlflow) when creating the dataset. Somes examples follow:

It enables logging either:
  - a list of int as a metric with incremental step, e.g ``[0.1,0.2,0.3]`` with ``mode=list`` for either ``save_args`` or ``load_args``

```python
from kedro_mlflow.io.metrics import MlflowMetricHistoryDataSet

metric_history_ds = MlflowMetricDataSet(key="my_metric", save_args={"mode": "list"})

with mlflow.start_run():
    metric_history_ds.save([0.1, 0.2, 0.3])  # will be logged with incremental steps
```
  - a dict of {step: value} as a metric:

```python
from kedro_mlflow.io.metrics import MlflowMetricHistoryDataSet

metric_history_ds = MlflowMetricDataSet(key="my_metric", save_args={"mode": "dict"})

with mlflow.start_run():
    metric_history_ds.save(
        {0: 0.1, 1: 0.2, 2: 0.3}
    )  # will be logged with incremental steps
```

  - a list of dict [{log_metric_arg: value}] as a metric, e.g:

```python
from kedro_mlflow.io.metrics import MlflowMetricHistoryDataSet

metric_history_ds = MlflowMetricDataSet(key="my_metric", save_args={"mode": "history"})

with mlflow.start_run():
    metric_history_ds.save(
        [
            {"step": 0, "value": 0.1, "timestamp": 1345545},
            {"step": 1, "value": 0.2, "timestamp": 1345546},
            {"step": 2, "value": 0.3, "timestamp": 1345547},
        ]
    )
```

You can combine the different mode for save and load, e.g:

```python
from kedro_mlflow.io.metrics import MlflowMetricHistoryDataSet

metric_history_ds = MlflowMetricDataSet(
    key="my_metric", save_args={"mode": "dict"}, save_args={"mode": "list"}
)

with mlflow.start_run():
    metric_history_ds.save(
        {0: 0.1, 1: 0.2, 2: 0.3}
    )  # will be logged with incremental steps
metric_history_ds.load()  # return [0.1,0.2,0.3]
```

As usual, since it is an ``AbstractDataSet``, it can be used with the YAML API in your ``catalog.yml``, and in this case, the ``key`` argument is optional:

```yaml
my_model_metric:
    type: kedro_mlflow.io.metrics.MlflowMetricHistoryDataSet
    run_id: 123456 # OPTIONAL, you should likely let it empty to log in the current run
    key: my_awesome_name # OPTIONAL: if not provided, the dataset name will be used (here "my_model_metric")
    load_args:
        mode: ... # OPTIONAL: "list" by default, one of {"list", "dict", "history"}
    save_args:
        mode: ... # OPTIONAL: "list" by default, one of {"list", "dict", "history"}
```

### Saving several metrics with their entire history with ``MlflowMetricsDataSet``

Since it is an ``AbstractDataSet``, it can be used with the YAML API. You can define it in your ``catalog.yml`` as:

```yaml
my_model_metrics:
    type: kedro_mlflow.io.metrics.MlflowMetricsDataSet
```

You can provide a prefix key, which is useful in situations like when you have multiple nodes producing metrics with the same names which you want to distinguish. If you are using the ``v``, it will handle that automatically for you by giving as prefix metrics data set name. In the example above the prefix would be ``my_model_metrics``.

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
        "metric2": [{"value": 1.1, "step": 1}, {"value": 1.2, "step": 2}],
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

Within a kedro run, the ``MlflowHook`` will automatically prefix the metrics datasets with their name in the catalog. In our example, the metrics will be stored in Mlflow with the following keys: ``my_model_metrics.metric1``, ``my_model_metrics.metric2``.

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
    return Pipeline(
        node(
            func=metrics_node,
            inputs=None,
            outputs="my_model_metrics",
            name="log_metrics",
        )
    )
```
