# Versioning Kedro DataSets

## What is artifact tracking?

Mlflow defines artifacts as "any data a user may want to track during code execution". This includes, but is not limited to:

- data needed for the model (e.g encoders, vectorizer, the machine learning model itself...)
- graphs (e.g. ROC or PR curve, importance variables, margins,  confusion matrix...)

Artifacts are a very flexible and convenient way to "bind" any data type to your code execution. Mlflow has a two-step process for such binding:

1. Persist the data locally in the desired file format
2. Upload the data to the [artifact store](./01_configuration.md)

## How to version data in a kedro project?

``kedro-mlflow`` introduces a new ``AbstractDataSet`` called ``MlflowArtifactDataSet``. It is a wrapper for any ``AbstractDataSet`` which decorates the underlying dataset ``save`` method and logs the file automatically in mlflow as an artifact each time the ``save`` method is called.

Since it is an ``AbstractDataSet``, it can be used with the YAML API. Assume that you have the following entry in the ``catalog.yml``:

```yaml
my_dataset_to_version:
    type: pandas.CSVDataSet
    filepath: /path/to/a/destination/file.csv
```

You can change it to:

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/LOCAL/destination/file.csv # must be a local file, wherever you want to log the data in the end
```

and this dataset will be automatically versioned in each pipeline execution.

## Frequently asked questions

### Can I pass extra parameters to the ``MlflowArtifactDataSet`` for finer control?

The ``MlflowArtifactDataSet`` takes a ``data_set`` argument which is a python dictionary passed to the ``__init__`` method of the dataset declared in ``type``. It means that you can pass any argument accepted by the underlying dataset in this dictionary. If you want to pass ``load_args`` and ``save_args`` in the previous example, add them in the ``data_set`` argument:

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
        load_args:
            sep: ;
        save_args:
            sep: ;
        # ... any other valid arguments for data_set
```

### Can I use the ``MlflowArtifactDataSet`` in interactive mode?

Like all Kedro ``AbstractDataSet``, ``MlflowArtifactDataSet`` is callable in the python API:

```python
from kedro_mlflow.io.artifacts import MlflowArtifactDataSet
from kedro.extras.datasets.pandas import CSVDataSet

csv_dataset = MlflowArtifactDataSet(
    data_set={
        "type": CSVDataSet,  # either a string "pandas.CSVDataSet" or the class
        "filepath": r"/path/to/a/local/destination/file.csv",
    }
)
csv_dataset.save(data=pd.DataFrame({"a": [1, 2], "b": [3, 4]}))
```

### How do I upload an artifact to a non local destination (e.g. an S3 or blog storage)?

The location where artifact will be stored does not depends of the logging function but rather on the artifact store specified when configuring the mlflow server. Read mlflow documentation to see:

- how to [configure a mlflow tracking server](https://www.mlflow.org/docs/latest/tracking.html#mlflow-tracking-servers)
- how to [configure an artifact store](https://www.mlflow.org/docs/latest/tracking.html#id10) with cloud storage.

Setting the `mlflow_tracking_uri` key of `mlflow.yml` to the url of this server is the only additional configuration you need to send your datasets to this remote server. Note that you still need to specify a **local** path for the underlying dataset, mlflow will take care of the upload to the server by itself.

You can refer to [this issue](https://github.com/Galileo-Galilei/kedro-mlflow/issues/15) for further details.

### Can I log an artifact in a specific run?

The ``MlflowArtifactDataSet`` has an extra attribute ``run_id`` which specifies the run you will log the artifact in. **Be cautious, because this argument will take precedence over the current run** when you call ``kedro run``, causing the artifact to be logged in another run that all the other data of the run.

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv  # must be a local filepath, no matter what is your actual mlflow storage (S3 or other)
    run_id: 13245678910111213  # a valid mlflow run to log in. If None, default to active run
```

### Can I reload an artifact from an existing run to use it in another run ?

You may want to reuse th artifact of a previous run to reuse it in another one, e.g. to continue training from a pretrained model, or to select the best model among several runs created during an hyperparamter tuning. The ``MlflowArtifactDataSet`` has an extra attribute ``run_id`` you can use to specify from which run you will load the artifact from. **Be cautious**, because:
- this argument will take precedence over the current run** when you call ``kedro run``, causing the artifact to be loaded from another run that all the other data of the run
- the artifact will be downloaded and erase the existing file at your local filepath

```yaml
my_dataset_to_reload:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv # must be a local filepath, no matter what is your actual mlflow storage (S3 or other)
    run_id: 13245678910111213  # a valid mlflow run with the existing artifact. It must be named "file.csv"
```

### Can I create a remote folder/subfolders architecture to organize the artifacts?

The ``MlflowArtifactDataSet`` has an extra argument ``artifact_path`` which specifies a remote subfolder where the artifact will be logged. It must be a relative path.

With below example, the artifact will be logged in mlflow within a `reporting` folder.

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
    artifact_path: reporting  # relative path where the remote artifact must be stored. if None, saved in root folder.
```
