# New ``DataSet``

## ``MlflowArtifactDataset``

``MlflowArtifactDataset`` is a wrapper for any ``AbstractDataset`` which logs the dataset automatically in mlflow as an artifact when its ``save`` method is called. It can be used both with the YAML API:

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataset
    dataset:
        type: pandas.CSVDataset  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
```

or with additional parameters:

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataset
    dataset:
        type: pandas.CSVDataset  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
        load_args:
            sep: ;
        save_args:
            sep: ;
        # ... any other valid arguments for dataset
    run_id: 13245678910111213  # a valid mlflow run to log in. If None, default to active run
    artifact_path: reporting  # relative path where the artifact must be stored. if None, saved in root folder.
```

or with the python API:

```python
from kedro_mlflow.io.artifacts import MlflowArtifactDataset
from kedro_datasets.pandas import CSVDataset

csv_dataset = MlflowArtifactDataset(
    dataset={"type": CSVDataset, "filepath": r"/path/to/a/local/destination/file.csv"}
)
csv_dataset.save(data=pd.DataFrame({"a": [1, 2], "b": [3, 4]}))
```

## Metrics `DataSets`

### ``MlflowMetricDataset``

[The ``MlflowMetricDataset`` is documented here](https://kedro-mlflow.readthedocs.io/en/latest/source/04_experimentation_tracking/05_version_metrics.html#saving-a-single-float-as-a-metric-with-mlflowmetricdataset).

### ``MlflowMetricHistoryDataset``

[The ``MlflowMetricHistoryDataset`` is documented here](https://kedro-mlflow.readthedocs.io/en/latest/source/04_experimentation_tracking/05_version_metrics.html#saving-a-single-float-as-a-metric-with-mlflowmetricdataset).


## Models `DataSets`

### ``MlflowModelTrackingDataset``

The ``MlflowModelTrackingDataset`` accepts the following arguments:

- flavor (str): Built-in or custom MLflow model flavor module. Must be Python-importable.
- run_id (Optional[str], optional): MLflow run ID to use to load the model from or save the model to. It plays the same role as "filepath" for standard mlflow datasets. Defaults to None.
- artifact_path (str, optional): the run relative path tothe model.
- pyfunc_workflow (str, optional): Either `python_model` or `loader_module`.See [mlflow workflows](https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#workflows).
- load_args (Dict[str, Any], optional): Arguments to `load_model` function from specified `flavor`. Defaults to None.
- save_args (Dict[str, Any], optional): Arguments to `log_model` function from specified `flavor`. Defaults to None.

You can either only specify the flavor:

```python
from kedro_mlflow.io.models import MlflowModelTrackingDataset
from sklearn.linear_model import LinearRegression

mlflow_model_tracking = MlflowModelTrackingDataset(flavor="mlflow.sklearn")
mlflow_model_tracking.save(LinearRegression())
```

Let assume that this first model has been saved once, and you xant to retrieve it (for prediction for instance):

```python
mlflow_model_tracking = MlflowModelTrackingDataset(
    flavor="mlflow.sklearn", run_id="<the-model-run-id>"
)
my_linear_regression = mlflow_model_tracking.load()
my_linear_regression.predict(
    data
)  # will obviously fail if you have not fitted your model object first :)
```

You can also specify some [logging parameters](https://www.mlflow.org/docs/latest/python_api/mlflow.sklearn.html#mlflow.sklearn.log_model):

```python
mlflow_model_tracking = MlflowModelTrackingDataset(
    flavor="mlflow.sklearn",
    run_id="<the-model-run-id>",
    save_args={
        "conda_env": {"python": "3.10.0", "dependencies": ["kedro==0.18.11"]},
        "input_example": data.iloc[0:5, :],
    },
)
mlflow_model_tracking.save(LinearRegression().fit(data))
```

As always with kedro, you can use it directly in the `catalog.yml` file:

```yaml
my_model:
    type: kedro_mlflow.io.models.MlflowModelTrackingDataset
    flavor: "mlflow.sklearn"
    run_id: <the-model-run-id>,
    save_args:
        conda_env:
            python: "3.10.0"
            dependencies:
                - "kedro==0.18.11"
```

### ``MlflowModelLocalFileSystemDataset``

The ``MlflowModelLocalFileSystemDataset`` accepts the following arguments:

- flavor (str): Built-in or custom MLflow model flavor module. Must be Python-importable.
- filepath (str): Path to store the dataset locally.
- pyfunc_workflow (str, optional): Either `python_model` or `loader_module`. See [mlflow workflows](https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#workflows).
- load_args (Dict[str, Any], optional): Arguments to `load_model` function from specified `flavor`. Defaults to None.
- save_args (Dict[str, Any], optional): Arguments to `save_model` function from specified `flavor`. Defaults to None.
- version (Version, optional): Kedro version to use. Defaults to None.

The use is very similar to ``MlflowModelTrackingDataset``, but you have to specify a local ``filepath`` instead of a `run_id`:

```python
from kedro_mlflow.io.models import MlflowModelTrackingDataset
from sklearn.linear_model import LinearRegression

mlflow_model_tracking = MlflowModelLocalFileSystemDataset(
    flavor="mlflow.sklearn", filepath="path/to/where/you/want/model"
)
mlflow_model_tracking.save(LinearRegression().fit(data))
```

The same arguments are available, plus an additional [`version` common to usual `AbstractVersionedDataset`](https://kedro.readthedocs.io/en/stable/kedro.io.AbstractVersionedDataset.html)

```python
mlflow_model_tracking = MlflowModelLocalFileSystemDataset(
    flavor="mlflow.sklearn",
    filepath="path/to/where/you/want/model",
    version="<valid-kedro-version>",
)
my_model = mlflow_model_tracking.load()
```

and with the YAML API in the `catalog.yml`:

```yaml
my_model:
    type: kedro_mlflow.io.models.MlflowModelLocalFileSystemDataset
    flavor: mlflow.sklearn
    filepath: path/to/where/you/want/model
    version: <valid-kedro-version>
```

### ``MlflowModelRegistryDataset``

The ``MlflowModelRegistryDataset`` accepts the following arguments:

- ``model_name`` (str): The name of the registered model is the mlflow registry
- ``stage_or_version`` (str): A valid stage (either "staging" or "production") or version number for the registred model.Default to None,(internally converted to "latest" if no alias si provided) which fetch the last version and the higher "stage" available.
- ``alias`` (str): A valid alias, which is used instead of stage to filter model since mlflow 2.9.0. Will raise an error if both ``stage_or_version`` and ``alias`` are provided.
- ``flavor`` (str): Built-in or custom MLflow model flavor module. Must be Python-importable.
- ``pyfunc_workflow`` (str, optional): Either `python_model` or `loader_module`. See [mlflow workflows](https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#workflows).
- ``load_args`` (Dict[str, Any], optional): Arguments to `load_model` function from specified `flavor`. Defaults to None.

We assume you have registered a mlflow model first, either [with the ``MlflowClient``](https://mlflow.org/docs/latest/model-registry.html#adding-an-mlflow-model-to-the-model-registry) or [within the mlflow ui](https://mlflow.org/docs/latest/model-registry.html#ui-workflow), e.g. :

```python
from sklearn.tree import DecisionTreeClassifier

import mlflow
import mlflow.sklearn

with mlflow.start_run():
    model = DecisionTreeClassifier()

    # Log the sklearn model and register as version 1
    mlflow.sklearn.log_model(
        sk_model=model, artifact_path="model", registered_model_name="my_awesome_model"
    )
```

You can fetch the model by its name:

```python
from kedro_mlflow.io.models import MlflowModelRegistryDataset

mlflow_model_tracking = MlflowModelRegistryDataset(model_name="my_awesome_model")
my_model = mlflow_model_tracking.load()
```

and with the YAML API in the `catalog.yml` (only for loading an existing model):

```yaml
my_model:
    type: kedro_mlflow.io.models.MlflowModelRegistryDataset
    model_name: my_awesome_model
```
