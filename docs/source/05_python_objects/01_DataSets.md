# New ``DataSet``:
## ``MlflowArtifactDataSet``
``MlflowArtifactDataSet`` is a wrapper for any ``AbstractDataSet`` which logs the dataset automatically in mlflow as an artifact when its ``save`` method is called. It can be used both with the YAML API:
```
my_dataset_to_version:
    type: kedro_mlflow.io.MlflowArtifactDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
```
or with additional parameters:
```
my_dataset_to_version:
    type: kedro_mlflow.io.MlflowArtifactDataSet
    data_set:
        type: pandas.CSVDataSet  # or any valid kedro DataSet
        filepath: /path/to/a/local/destination/file.csv
        load_args:
            sep: ;
        save_args:
            sep: ;
        # ... any other valid arguments for data_set
    run_id: 13245678910111213  # a valid mlflow run to log in. If None, default to active run
    artifact_path: reporting  # relative path where the artifact must be stored. if None, saved in root folder.
```
or with the python API:
```
from kedro_mlflow.io import MlflowArtifactDataSet
from kedro.extras.datasets.pandas import CSVDataSet
csv_dataset = MlflowArtifactDataSet(data_set={"type": CSVDataSet,
                                      "filepath": r"/path/to/a/local/destination/file.csv"})
csv_dataset.save(data=pd.DataFrame({"a":[1,2], "b": [3,4]}))
```
