from pathlib import Path

import mlflow
import pandas as pd
import pytest
from kedro.extras.datasets.pandas import CSVDataSet
from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io import PartitionedDataSet
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
def df2():
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
def test_mlflow_csv_pkl_dataset_save_reload(
    tmp_path, tracking_uri, dataset, extension, data, artifact_path
):
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    filepath = (tmp_path / "data").with_suffix(extension)

    mlflow_dataset = MlflowArtifactDataSet(
        artifact_path=artifact_path,
        data_set=dict(type=dataset, filepath=filepath.as_posix()),
    )

    with mlflow.start_run():
        mlflow_dataset.save(data)
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
    assert data.equals(mlflow_dataset.load())


@pytest.mark.parametrize(
    "exists_active_run",
    [(False), (True)],
)
def test_artifact_dataset_save_with_run_id(
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

    with mlflow.start_run():

        run_id = mlflow.active_run().info.run_id

        mlflow_csv_dataset = MlflowArtifactDataSet(
            data_set=dict(
                type=CSVDataSet,
                filepath=(tmp_path / "df1.csv").as_posix(),
                versioned=True,
            ),
            # run_id=run_id,
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

        assert df1.equals(mlflow_csv_dataset.load())  # and must loadable


def test_artifact_dataset_logging_deactivation(tmp_path, tracking_uri):
    mlflow_pkl_dataset = MlflowArtifactDataSet(
        data_set=dict(type=PickleDataSet, filepath=(tmp_path / "df1.csv").as_posix())
    )

    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())

    mlflow_pkl_dataset._logging_activated = False

    all_runs_id_beginning = set(
        [
            run.run_id
            for k in range(len(mlflow_client.list_experiments()))
            for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
        ]
    )

    mlflow_pkl_dataset.save(2)

    all_runs_id_end = set(
        [
            run.run_id
            for k in range(len(mlflow_client.list_experiments()))
            for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
        ]
    )

    assert all_runs_id_beginning == all_runs_id_end


def test_mlflow_artifact_logging_deactivation_is_bool(tmp_path):
    mlflow_csv_dataset = MlflowArtifactDataSet(
        data_set=dict(type=CSVDataSet, filepath=(tmp_path / "df1.csv").as_posix())
    )

    with pytest.raises(ValueError, match="_logging_activated must be a boolean"):
        mlflow_csv_dataset._logging_activated = "hello"


def test_artifact_dataset_load_with_run_id(tmp_path, tracking_uri, df1, df2):

    mlflow.set_tracking_uri(tracking_uri.as_uri())

    # define the logger
    mlflow_csv_dataset = MlflowArtifactDataSet(
        data_set=dict(type=CSVDataSet, filepath=(tmp_path / "df.csv").as_posix())
    )

    # create a first run, save a first dataset
    with mlflow.start_run():
        run_id1 = mlflow.active_run().info.run_id
        mlflow_csv_dataset.save(df1)

    # saving a second time will erase local dataset
    with mlflow.start_run():
        mlflow_csv_dataset.save(df2)

    # if we load the dataset, it will be equal to the seond one, using the local filepath
    assert df2.equals(mlflow_csv_dataset.load())

    # update the logger and reload outside of an mlflow run : it should load the dataset if the first run id
    mlflow_csv_dataset.run_id = run_id1
    assert df1.equals(mlflow_csv_dataset.load())


@pytest.mark.parametrize("artifact_path", (None, "folder", "folder/subfolder"))
def test_artifact_dataset_load_with_run_id_and_artifact_path(
    tmp_path, tracking_uri, df1, artifact_path
):
    mlflow.set_tracking_uri(tracking_uri.as_uri())

    # save first and retrieve run id
    mlflow_csv_dataset1 = MlflowArtifactDataSet(
        data_set=dict(type=CSVDataSet, filepath=(tmp_path / "df1.csv").as_posix()),
        artifact_path=artifact_path,
    )
    with mlflow.start_run():
        mlflow_csv_dataset1.save(df1)
        first_run_id = mlflow.active_run().info.run_id
        (
            tmp_path / "df1.csv"
        ).unlink()  # we need to delete the data, else it is automatically reused instead of downloading
    # same as before, but a closed run_id is specified
    mlflow_csv_dataset2 = MlflowArtifactDataSet(
        data_set=dict(type=CSVDataSet, filepath=(tmp_path / "df1.csv").as_posix()),
        artifact_path=artifact_path,
        run_id=first_run_id,
    )

    assert df1.equals(mlflow_csv_dataset2.load())
    assert df1.equals(
        mlflow_csv_dataset2.load()
    )  # we check idempotency. When using a local tracking uri, mlflow does not downlaod in a tempfolder, so moving the folder alter the mlflow run


@pytest.mark.parametrize("artifact_path", [None, "partitioned_data"])
def test_partitioned_dataset_save_and_reload(
    tmp_path, tracking_uri, artifact_path, df1, df2
):

    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())

    mlflow_dataset = MlflowArtifactDataSet(
        artifact_path=artifact_path,
        data_set=dict(
            type=PartitionedDataSet,
            path=(tmp_path / "df_dir").as_posix(),
            dataset="pandas.CSVDataSet",
            filename_suffix=".csv",
        ),
    )

    data = dict(df1=df1, df2=df2)

    with mlflow.start_run():
        mlflow_dataset.save(data)
        run_id = mlflow.active_run().info.run_id

    # the artifact must be properly uploaded to "mlruns" and reloadable
    artifact_path_df_dir = f"{artifact_path}/df_dir" if artifact_path else "df_dir"
    run_artifacts = [
        fileinfo.path
        for fileinfo in mlflow_client.list_artifacts(
            run_id=run_id,
            path=artifact_path_df_dir,
        )
    ]
    for df_name in data.keys():
        remote_path = (
            f"df_dir/{df_name}.csv"
            if artifact_path is None
            else (Path(artifact_path) / "df_dir" / df_name)
            .with_suffix(".csv")
            .as_posix()
        )
        assert remote_path in run_artifacts

    reloaded_data = {k: loader() for k, loader in mlflow_dataset.load().items()}
    for k, df in data.items():
        pd.testing.assert_frame_equal(df, reloaded_data[k])
