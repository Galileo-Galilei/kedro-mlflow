# Version model

## What is model tracking?

MLflow allows to serialize and deserialize models to a common format, track those models in MLflow Tracking and manage them using MLflow Model Registry. Many popular Machine / Deep Learning frameworks have built-in support through what MLflow calls [flavors](https://www.mlflow.org/docs/latest/models.html#built-in-model-flavors). Even if there is no flavor for your framework of choice, it is easy to [create your own flavor](https://www.mlflow.org/docs/latest/models.html#custom-python-models) and integrate it with MLflow.

## How to track models using MLflow in Kedro project?

`kedro-mlflow` introduces two new `DataSet` types that can be used in `DataCatalog` called `MlflowModelLoggerDataSet` and `MlflowModelSaverDataSet`. The two have very similar API, except that:

- the ``MlflowModelLoggerDataSet`` is used to load from and save to from the mlflow artifact store. It uses optional `run_id` argument to load and save from a given `run_id` which must exists in the mlflow server you are logging to.
- the ``MlflowModelSaverDataSet`` is used to load from and save to a given path. It uses the standard `filepath` argument in the constructor of Kedro DataSets. Note that it **does not log in mlflow**.

*Note: If you use ``MlflowModelLoggerDataSet``, it will be saved during training in your current run. However, you will need to specify the run id to predict with (since it is not persisted locally, it will not pick the latest model by default). You may prefer to combine ``MlflowModelSaverDataSet`` and ``MlflowArtifactDataSet`` to make persist it both locally and remotely, see further.*

Suppose you would like to register a `scikit-learn` model of your `DataCatalog` in mlflow, you can use the following yaml API:

```yaml
my_sklearn_model:
    type: kedro_mlflow.io.models.MlflowModelLoggerDataSet
    flavor: mlflow.sklearn
```

More informations on available parameters are available in the [dedicated section](../07_python_objects/01_DataSets.md#mlflowmodelloggerdataset).

You are now able to use ``my_sklearn_model`` in your nodes. Since this model is registered in mlflow, you can also leverage the [mlflow model serving abilities](https://www.mlflow.org/docs/latest/cli.html#mlflow-models-serve) or [predicting on batch abilities](https://www.mlflow.org/docs/latest/cli.html#mlflow-models-predict), as well as the [mlflow models registry](https://www.mlflow.org/docs/latest/model-registry.html) to manage the lifecycle of this model.

## Frequently asked questions?

### How is it working under the hood?

**For ``MlflowModelLoggerDataSet``**

During save, a model object from node output is logged to mlflow using ``log_model`` function of the specified ``flavor``. It is logged in the `run_id` run if specified and if there is no active run, else in the currently active mlflow run. If the `run_id` is specified and there is an active run, the saving operation will fail. Consequently it will **never be possible to save in a specific mlflow run_id** if you launch a pipeline with the `kedro run` command because the `MlflowHook` creates a new run before each pipeline run.

During load, the model is retrieved from the ``run_id`` if specified, else it is retrieved from the mlflow active run. If there is no mlflow active run, the loading fails. This will never happen if you are using the `kedro run` command, because the `MlflowHook` creates a new run before each pipeline run.

**For ``MlflowModelSaverDataSet``**

During save, a model object from node output is saved locally under specified ``filepath`` using ``save_model`` function of the specified ``flavor``.

When model is loaded, the latest version stored locally is read using ``load_model`` function of the specified ``flavor``. You can also load a model from a specific kedro run by specifying the `version` argument to the constructor.

### How can I track a custom MLflow model flavor?

To track a custom MLflow model flavor you need to set the `flavor` parameter to import the module of your custom flavor and to specify a [pyfunc workflow](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#pyfunc-create-custom-workflows) which can be set either to `python_model` or `loader_module`. The former is the more high level and user friendly and is [recommend by mlflow](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#which-workflow-is-right-for-my-use-case) while the latter offer more control. We haven't tested the integration in `kedro-mlflow` of this second workflow extensively, and it should be used with caution.

```yaml
my_custom_model:
    type: kedro_mlflow.io.models.MlflowModelLoggerDataSet
    flavor: my_package.custom_mlflow_flavor
    pyfunc_workflow: python_model # or loader_module
```

### How can I save model locally and log it in MLflow in one step?

If you want to save your model both locally and remotely within the same run, you can leverage `MlflowArtifactDataSet`:

```yaml
sklearn_model:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataSet
    data_set:
        type: kedro_mlflow.io.models.MlflowModelSaverDataSet
        flavor: mlflow.sklearn
        filepath: data/06_models/sklearn_model
```

This might be useful if you want to always read the lastest model saved locally and log it to MLflow each time the new model is being trained for tracking purpose.
