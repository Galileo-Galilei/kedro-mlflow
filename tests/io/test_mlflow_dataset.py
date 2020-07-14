import mlflow
import pandas as pd
import pytest
from kedro.extras.datasets.pandas import CSVDataSet

from kedro_mlflow.io import MlflowDataSet


@pytest.fixture
def tracking_uri(tmp_path):
    return tmp_path / "mlruns"


@pytest.fixture
def dummy_df1():
    return pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})


@pytest.fixture
def dummy_df2():
    return pd.DataFrame({"col3": [7, 8, 9], "col4": ["a", "b", "c"]})


def test_mlflow_csv_data_set_save(tmp_path, tracking_uri, dummy_df1):
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_csv_dataset = MlflowDataSet(
        data_set=dict(type=CSVDataSet, filepath=(tmp_path / "df1.csv").as_posix())
    )
    with mlflow.start_run():
        mlflow_csv_dataset.save(dummy_df1)
        run_id = mlflow.active_run().info.run_id

    # the artifact must be properly uploaded to "mlruns" and reloadable
    assert (tracking_uri / "0" / run_id / "artifacts" / "df1.csv").is_file()
    assert dummy_df1.equals(mlflow_csv_dataset.load())


def test_mlflow_data_set_save_with_run_id(tmp_path, tracking_uri, dummy_df1):
    mlflow.set_tracking_uri(tracking_uri.as_uri())

    # create a first run and get its id
    with mlflow.start_run():
        mlflow.log_param("fake", 2)
        run_id = mlflow.active_run().info.run_id

    # then same scenario but precise the run_id where data is saved
    mlflow_csv_dataset = MlflowDataSet(
        data_set=dict(type=CSVDataSet, filepath=(tmp_path / "df1.csv").as_posix()),
        run_id=run_id,
    )
    mlflow_csv_dataset.save(dummy_df1)
    tracked_runs = [f.stem for f in (tracking_uri / "0").glob("*") if f.is_dir()]
    # same tests as previously, bu no new experiments must have been created
    assert len(tracked_runs) == 1
    assert (tracking_uri / "0" / run_id / "artifacts" / "df1.csv").is_file()
    assert dummy_df1.equals(mlflow_csv_dataset.load())


# use pytest.fixture.parametrize to test if it works with
# - type="pandas.CSVDataSet" (a string) -> because it is necessary for loading from catalog
# - experiment name = None or a string
