# Version model

## What is model tracking?

MLflow allows to serialize and deserialize models to a common format, track those models in MLflow Tracking and manage them using MLflow Model Registry. Many popular Machine / Deep Learning frameworks have built-in support through what MLflow calls flavors. Even if there's no flavor for your framework of choice, it's easy to create your own flavor and integrate it with MLflow.

## How to track models using MLflow in Kedro project?

kedro-mlflow introduces a new dataset type that can be used in Data Catalog called ``MlflowModelDataSet``. Suppose you would like to add a scikit-learn model to your Data Catalog. For that you need to an entry like this:

```yaml
my_sklearn_model:
    type: kedro_mlflow.io.MlflowModelDataSet
    flavor: mlflow.sklearn
    path: data/06_models/my_sklearn_model
```

You are now able to use ``my_sklearn_model`` in your nodes.

## Frequently asked questions?

## How is it working under the hood?

During save, a model object from node output is save locally under specified ``path`` using ``save_model`` function of the specified ``flavor``. It is then logged to MLflow using ``log_model``.

When model is loaded, the latest version stored locally is read using ``load_model`` function of the specified ``flavor``. You can also load a model from a specific [Kedro run](#can-i-use-kedro-versioning-with-mlflowmodeldataset) or [MLflow run](#can-i-load-a-model-from-a-specific-mlflow-run-id).

### How can I track a custom MLflow model flavor?

To track a custom MLflow model flavor you need to set the `flavor` parameter to import path of your custom flavor:

```yaml
my_custom_model:
    type: kedro_mlflow.io.MlflowModelDataSet
    flavor: my_package.custom_mlflow_flavor
    path: data/06_models/my_sklearn_model
```

### Can I use Kedro versioning with `MlflowModelDataSet`?

### Can I load a model from a specific MLflow Run ID?
