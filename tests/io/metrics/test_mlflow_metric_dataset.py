import mlflow
import pytest
from kedro.io.core import DataSetError
from mlflow.tracking import MlflowClient

from kedro_mlflow.io.metrics import MlflowMetricDataSet


@pytest.fixture
def mlflow_tracking_uri(tmp_path):
    tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(tracking_uri)
    return tracking_uri


@pytest.fixture
def mlflow_client(mlflow_tracking_uri):
    mlflow_client = MlflowClient(mlflow_tracking_uri)
    return mlflow_client


def test_mlflow_wrong_save_mode():
    with pytest.raises(DataSetError, match=r"save_args\['mode'\] must be one of"):
        metric_ds = MlflowMetricDataSet(key="my_metric", save_args={"mode": "bad_mode"})
        with mlflow.start_run():
            metric_ds.save(0.3)


def test_mlflow_metric_dataset_save_without_active_run_or_run_id():
    metric_ds = MlflowMetricDataSet(key="my_metric")
    with pytest.raises(
        DataSetError,
        match="You must either specify a run_id or have a mlflow active run opened",
    ):
        metric_ds.save(0.3)


@pytest.mark.parametrize(
    "save_args",
    [
        (None),
        ({}),
        ({"mode": "append"}),
        ({"mode": "overwrite"}),
        ({"step": 2}),
        ({"step": 2, "mode": "append"}),
    ],
)
def test_mlflow_metric_dataset_save_with_active_run(mlflow_client, save_args):
    metric_ds = MlflowMetricDataSet(key="my_metric", save_args=save_args)
    with mlflow.start_run():
        metric_ds.save(0.3)
        run_id = mlflow.active_run().info.run_id
        metric_history = mlflow_client.get_metric_history(run_id, "my_metric")

        step = 0 if save_args is None else save_args.get("step", 0)
        assert [
            (metric.key, metric.step, metric.value) for metric in metric_history
        ] == [("my_metric", step, 0.3)]


@pytest.mark.parametrize(
    "save_args",
    [
        (None),
        ({}),
        ({"mode": "append"}),
        ({"mode": "overwrite"}),
        ({"step": 2}),
        ({"step": 2, "mode": "append"}),
    ],
)
def test_mlflow_metric_dataset_save_with_run_id(mlflow_client, save_args):

    # this time, the run is created first and closed
    # the MlflowMetricDataSet should reopen it to interact
    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id

    metric_ds = MlflowMetricDataSet(run_id=run_id, key="my_metric", save_args=save_args)
    metric_ds.save(0.3)
    metric_history = mlflow_client.get_metric_history(run_id, "my_metric")
    step = 0 if save_args is None else save_args.get("step", 0)
    assert [(metric.key, metric.step, metric.value) for metric in metric_history] == [
        ("my_metric", step, 0.3)
    ]
    assert mlflow.active_run() is None  # no run should be opened


def test_mlflow_metric_dataset_save_append_mode(mlflow_client):

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id

    metric_ds = MlflowMetricDataSet(
        run_id=run_id, key="my_metric", save_args={"mode": "append"}
    )

    metric_ds.save(0.3)
    metric_ds.save(1)
    metric_history = mlflow_client.get_metric_history(run_id, "my_metric")
    assert [(metric.key, metric.step, metric.value) for metric in metric_history] == [
        ("my_metric", 0, 0.3),
        ("my_metric", 1, 1),
    ]


def test_mlflow_metric_dataset_save_overwrite_mode(mlflow_client):

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id

    # overwrite is the default mode
    metric_ds = MlflowMetricDataSet(run_id=run_id, key="my_metric")

    metric_ds.save(0.3)
    metric_ds.save(1)
    metric_history = mlflow_client.get_metric_history(run_id, "my_metric")
    assert [(metric.key, metric.step, metric.value) for metric in metric_history] == [
        ("my_metric", 0, 0.3),
        ("my_metric", 0, 1),  # same step
    ]


def test_mlflow_metric_dataset_load():

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow.log_metric(key="awesome_metric", value=0.1)

    # overwrite is the default mode
    metric_ds = MlflowMetricDataSet(run_id=run_id, key="awesome_metric")

    assert metric_ds.load() == 0.1


def test_mlflow_metric_dataset_load_last_logged_by_default_if_unordered():

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow.log_metric(key="awesome_metric", value=0.4, step=3)
        mlflow.log_metric(key="awesome_metric", value=0.3, step=2)
        mlflow.log_metric(key="awesome_metric", value=0.2, step=1)
        mlflow.log_metric(key="awesome_metric", value=0.1, step=0)

    # overwrite is the default mode
    metric_ds = MlflowMetricDataSet(run_id=run_id, key="awesome_metric")

    assert (
        metric_ds.load() == 0.1
    )  # the last value is retrieved even if it has a smaller step


def test_mlflow_metric_dataset_load_given_step():

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow.log_metric(key="awesome_metric", value=0.1, step=0)
        mlflow.log_metric(key="awesome_metric", value=0.2, step=1)
        mlflow.log_metric(key="awesome_metric", value=0.3, step=2)
        mlflow.log_metric(key="awesome_metric", value=0.4, step=3)

    # overwrite is the default mode
    metric_ds = MlflowMetricDataSet(
        run_id=run_id, key="awesome_metric", load_args={"step": 2}
    )

    assert metric_ds.load() == 0.3


def test_mlflow_metric_dataset_load_last_given_step_if_duplicated():

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow.log_metric(key="awesome_metric", value=0.1, step=0)
        mlflow.log_metric(key="awesome_metric", value=0.2, step=1)
        mlflow.log_metric(key="awesome_metric", value=0.3, step=2)
        mlflow.log_metric(key="awesome_metric", value=0.31, step=2)
        mlflow.log_metric(key="awesome_metric", value=0.32, step=2)
        mlflow.log_metric(key="awesome_metric", value=0.4, step=3)

    # overwrite is the default mode
    metric_ds = MlflowMetricDataSet(
        run_id=run_id, key="awesome_metric", load_args={"step": 2}
    )

    assert metric_ds.load() == 0.32


def test_mlflow_metric_dataset_logging_deactivation(mlflow_tracking_uri):
    metric_ds = MlflowMetricDataSet(key="inactive_metric")
    metric_ds._logging_activated = False
    with mlflow.start_run():
        metric_ds.save(1)
        assert metric_ds._exists() is False


def test_mlflow_metric_logging_deactivation_is_bool():
    mlflow_metric_dataset = MlflowMetricDataSet(key="hello")

    with pytest.raises(ValueError, match="_logging_activated must be a boolean"):
        mlflow_metric_dataset._logging_activated = "hello"
