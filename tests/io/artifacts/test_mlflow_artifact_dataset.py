from pathlib import Path

import mlflow
import pandas as pd
import pytest
from kedro.extras.datasets.pandas import CSVDataSet
from kedro.extras.datasets.pickle import PickleDataSet
from mlflow.tracking import MlflowClient
from pytest_lazyfixture import lazy_fixture

from kedro_mlflow.io.artifacts import MlflowArtifactDataSet


@pytest.fixture
def tracking_uri(tmp_path):
    return tmp_path / "mlruns"


@pytest.fixture
def df1():
    return pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})


@pytest.fixture
def dummy_df2():
    return pd.DataFrame({"col3": [7, 8, 9], "col4": ["a", "b", "c"]})


@pytest.mark.parametrize(
    "dataset,extension,data,artifact_path",
    [
        (CSVDataSet, ".csv", lazy_fixture("df1"), None),
        ("pandas.CSVDataSet", ".csv", lazy_fixture("df1"), None),
        (PickleDataSet, ".pkl", lazy_fixture("df1"), None),
        ("pickle.PickleDataSet", ".pkl", lazy_fixture("df1"), None),
        (CSVDataSet, ".csv", lazy_fixture("df1"), "artifact_dir"),
        ("pandas.CSVDataSet", ".csv", lazy_fixture("df1"), "artifact_dir"),
        (PickleDataSet, ".pkl", lazy_fixture("df1"), "artifact_dir"),
        (
            "pickle.PickleDataSet",
            ".pkl",
            lazy_fixture("df1"),
            "artifact_dir",
        ),
    ],
)
def test_mlflow_csv_data_set_save_reload(
    tmp_path, tracking_uri, dataset, extension, data, artifact_path
):
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    filepath = (tmp_path / "data").with_suffix(extension)

    mlflow_csv_dataset = MlflowArtifactDataSet(
        artifact_path=artifact_path,
        data_set=dict(type=CSVDataSet, filepath=filepath.as_posix()),
    )

    with mlflow.start_run():
        mlflow_csv_dataset.save(data)
        run_id = mlflow.active_run().info.run_id

    # the artifact must be properly uploaded to "mlruns" and reloadable
    run_artifacts = [
        fileinfo.path
        for fileinfo in mlflow_client.list_artifacts(run_id=run_id, path=artifact_path)
    ]
    remote_path = (
        filepath.name
        if artifact_path is None
        else (Path(artifact_path) / filepath.name).as_posix()
    )
    assert remote_path in run_artifacts
    assert data.equals(mlflow_csv_dataset.load())


@pytest.mark.parametrize(
    "exists_active_run",
    [(False), (True)],
)
def test_mlflow_data_set_save_with_run_id(
    tmp_path, tracking_uri, df1, exists_active_run
):
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    nb_runs = 0
    # create a first run and get its id
    with mlflow.start_run():
        mlflow.log_param("fake", 2)
        run_id = mlflow.active_run().info.run_id
        nb_runs += 1

    # check behaviour when logging with an already opened run
    if exists_active_run:
        mlflow.start_run()
        active_run_id = mlflow.active_run().info.run_id
        nb_runs += 1

    # then same scenario but the run_id where data is saved is specified
    mlflow_csv_dataset = MlflowArtifactDataSet(
        data_set=dict(type=CSVDataSet, filepath=(tmp_path / "df1.csv").as_posix()),
        run_id=run_id,
    )
    mlflow_csv_dataset.save(df1)

    # same tests as previously, bu no new experiments must have been created
    runs_list = mlflow_client.list_run_infos(experiment_id="0")
    run_artifacts = [
        fileinfo.path for fileinfo in mlflow_client.list_artifacts(run_id=run_id)
    ]

    assert len(runs_list) == nb_runs  # no new run must have been created when saving
    assert (
        mlflow.active_run().info.run_id == active_run_id
        if mlflow.active_run()
        else True
    )  # if a run was opened before saving, it must be reopened
    assert "df1.csv" in run_artifacts  # the file must exists
    assert df1.equals(mlflow_csv_dataset.load())  # and must loadable

    if exists_active_run:
        mlflow.end_run()


def test_is_versioned_dataset_logged_correctly_in_mlflow(tmp_path, tracking_uri, df1):
    """Check if versioned dataset is logged correctly in MLflow as artifact.

    For versioned datasets just artifacts from current run should be logged.
    """
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())

    mlflow.start_run()

    run_id = mlflow.active_run().info.run_id
    active_run_id = mlflow.active_run().info.run_id

    mlflow_csv_dataset = MlflowArtifactDataSet(
        data_set=dict(
            type=CSVDataSet, filepath=(tmp_path / "df1.csv").as_posix(), versioned=True
        ),
        run_id=run_id,
    )
    mlflow_csv_dataset.save(df1)

    run_artifacts = [
        fileinfo.path for fileinfo in mlflow_client.list_artifacts(run_id=run_id)
    ]

    # Check if just one artifact was created in given run.
    assert len(run_artifacts) == 1

    artifact_path = mlflow_client.download_artifacts(
        run_id=run_id, path=run_artifacts[0]
    )

    # Check if saved artifact is file and not folder where versioned datasets are stored.
    assert Path(artifact_path).is_file()

    assert (
        mlflow.active_run().info.run_id == active_run_id
        if mlflow.active_run()
        else True
    )  # if a run was opened before saving, it must be reopened
    assert df1.equals(mlflow_csv_dataset.load())  # and must loadable

    mlflow.end_run()
