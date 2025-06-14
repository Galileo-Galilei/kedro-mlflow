# Track Datasets as artifacts

## What is artifact tracking?

Mlflow defines artifacts as "any data a user may want to track during code execution". This includes, but is not limited to:

- data needed for the model (e.g encoders, vectorizer, the machine learning model itself...)
- graphs (e.g. ROC or PR curve, importance variables, margins,  confusion matrix...)

Artifacts are a very flexible and convenient way to "bind" any data type to your code execution. Mlflow has a two-step process for such binding:

1. Persist the data locally in the desired file format
2. Upload the data to the [artifact store](https://kedro-mlflow.readthedocs.io/en/latest/source/03_experiment_tracking/01_experiment_tracking/01_configuration.html)

## How to track data in a kedro project?

``kedro-mlflow`` introduces a new ``AbstractDataset`` called ``MlflowArtifactDataset``. It is a wrapper for any ``AbstractDataset`` which decorates the underlying dataset ``save`` method and logs the file automatically in mlflow as an artifact each time the ``save`` method is called.

Since it is an ``AbstractDataset``, it can be used with the YAML API. Assume that you have the following entry in the ``catalog.yml``:

```yaml
my_dataset_to_track:
    type: pandas.CSVDataset
    filepath: /path/to/a/destination/file.csv
```

You can change it to:

```yaml
my_dataset_to_track:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataset
    dataset:
        type: pandas.CSVDataset  # or any valid kedro DataSet
        filepath: /path/to/a/LOCAL/destination/file.csv # must be a local file, wherever you want to log the data in the end
```

and this dataset will be automatically versioned in each pipeline execution.

## Frequently asked questions


:::{dropdown} Can I pass extra parameters to the ``MlflowArtifactDataset`` for finer control?

The ``MlflowArtifactDataset`` takes a ``dataset`` argument which is a python dictionary passed to the ``__init__`` method of the dataset declared in ``type``. It means that you can pass any argument accepted by the underlying dataset in this dictionary. If you want to pass ``load_args`` and ``save_args`` in the previous example, add them in the ``dataset`` argument:

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
```

:::

:::{dropdown} Can I use the ``MlflowArtifactDataset`` in interactive mode?

Like all Kedro ``AbstractDataset``, ``MlflowArtifactDataset`` is callable in the python API:

```python
from kedro_mlflow.io.artifacts import MlflowArtifactDataset
from kedro_datasets.pandas import CSVDataset

csv_dataset = MlflowArtifactDataSet(
    dataset={
        "type": CSVDataset,  # either a string "pandas.CSVDataset" or the class
        "filepath": r"/path/to/a/local/destination/file.csv",
    }
)
csv_dataset.save(data=pd.DataFrame({"a": [1, 2], "b": [3, 4]}))
```
:::


:::{dropdown} How do I upload an artifact to a non local destination (e.g. an S3 or blog storage)?

The location where artifact will be stored does not depends of the logging function but rather on the artifact store specified when configuring the mlflow server. Read mlflow documentation to see:

- how to [configure a mlflow tracking server](https://www.mlflow.org/docs/latest/tracking.html#mlflow-tracking-servers)
- how to [configure an artifact store](https://www.mlflow.org/docs/latest/tracking.html#id10) with cloud storage.

**Setting the `mlflow_tracking_uri` key of `mlflow.yml` to the url of this properly configured server** is the only additional configuration you need to send your datasets to this remote server.

```{important}
You still need to specify a **local** path for the underlying dataset (even to store it on a remote storage), mlflow will take care of the upload to the server by itself.
```

You can refer to [this issue](https://github.com/Galileo-Galilei/kedro-mlflow/issues/15) for further details.
:::

:::{dropdown} Can I log an artifact in a specific run?

The ``MlflowArtifactDataset`` has an extra attribute ``run_id`` which specifies the run you will log the artifact in. **Be cautious, because this argument will take precedence over the current run** when you call ``kedro run``, causing the artifact to be logged in another run that all the other data of the run.

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataset
    dataset:
        type: pandas.CSVDataset  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv  # must be a local filepath, no matter what is your actual mlflow storage (S3 or other)
    run_id: 13245678910111213  # a valid mlflow run to log in. If None, default to active run
```

:::

:::{dropdown} Can I reload an artifact from an existing run to use it in another run ?

You may want to reuse th artifact of a previous run to reuse it in another one, e.g. to continue training from a pretrained model, or to select the best model among several runs created during an hyperparamter tuning. The ``MlflowArtifactDataset`` has an extra attribute ``run_id`` you can use to specify from which run you will load the artifact from. **Be cautious**, because:
- this argument will take precedence over the current run** when you call ``kedro run``, causing the artifact to be loaded from another run that all the other data of the run
- the artifact will be downloaded and erase the existing file at your local filepath

```yaml
my_dataset_to_reload:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataset
    dataset:
        type: pandas.CSVDataset  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv # must be a local filepath, no matter what is your actual mlflow storage (S3 or other)
    run_id: 13245678910111213  # a valid mlflow run with the existing artifact. It must be named "file.csv"
```
:::

:::{dropdown} Can I create a remote folder/subfolders architecture to organize the artifacts?

The ``MlflowArtifactDataset`` has an extra argument ``artifact_path`` which specifies a remote subfolder where the artifact will be logged. It must be a relative path.

With below example, the artifact will be logged in mlflow within a `reporting` folder.

```yaml
my_dataset_to_version:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataset
    dataset:
        type: pandas.CSVDataset  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
    artifact_path: reporting  # relative path where the remote artifact must be stored. if None, saved in root folder.
```

:::

:::{dropdown} Why does my ``PartitionedDataset`` log partitions from all previous runs?

Kedro provides a few datasets saving results in partitions (i.e., multiple files),
most notably the ``PartitionedDataset`` and ``MatplotlibDataset``.

Both would by default **not** delete partitions generated by previous runs if those
from the current run don't overwrite exactly the same filenames.

However, for experiment tracking purposes, you would typically want to wipe all previously
saved partitions, and log only those produced by current run.

This can be achieved by specifying `overwrite: true` in dataset specification, like so:

```yaml
profiling.partitioned_scatterplots:
    type: kedro_mlflow.io.artifacts.MlflowArtifactDataset
    artifact_path: profiling
    dataset:
        type: matplotlib.MatplotlibDataset
        filepath: data/08_reporting/partitioned_scatterplots/
        overwrite: true  # Defaults to false, but we change it to ensure reproducibility
```

There is an ongoing discussion that maybe `true` should be the default,
you can follow it [here](https://github.com/kedro-org/kedro-plugins/issues/1101).

:::
