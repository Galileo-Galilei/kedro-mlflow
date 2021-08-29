import mlflow
import pytest
from mlflow.tracking import MlflowClient

from kedro_mlflow.io.metrics import MlflowMetricHistoryDataSet


@pytest.fixture
def mlflow_tracking_uri(tmp_path):
    tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(tracking_uri)
    return tracking_uri


@pytest.fixture
def mlflow_client(mlflow_tracking_uri):
    mlflow_client = MlflowClient(mlflow_tracking_uri)
    return mlflow_client


@pytest.mark.parametrize(
    "save_mode,load_mode",
    [
        ("list", "list"),
        ("list", "dict"),
        ("dict", "list"),
        ("dict", "dict"),
        ("history", "list"),
        ("history", "dict"),
        ("history", "history"),
    ],
)
def test_mlflow_metric_history_dataset_save_load(mlflow_client, save_mode, load_mode):
    metric_as_list = [0.3, 0.2, 0.1, 0.15, 0.05]
    metric_as_dict = dict(enumerate(metric_as_list))
    metric_as_history = [
        {"step": i, "value": value, "timestamp": 1630235933 + i}
        for i, value in metric_as_dict.items()
    ]

    mode_metrics_mapping = {
        "list": metric_as_list,
        "dict": metric_as_dict,
        "history": metric_as_history,
    }

    metric_ds_saver = MlflowMetricHistoryDataSet(
        key="my_metric", save_args={"mode": save_mode}
    )
    with mlflow.start_run():
        metric_ds_saver.save(mode_metrics_mapping[save_mode])
        run_id = mlflow.active_run().info.run_id

    # check existence
    run = mlflow_client.get_run(run_id)
    assert "my_metric" in run.data.metrics.keys()

    metric_ds_loader = MlflowMetricHistoryDataSet(
        key="my_metric", run_id=run_id, load_args={"mode": load_mode}
    )

    assert metric_ds_loader.load() == mode_metrics_mapping[load_mode]


def test_mlflow_metric_history_dataset_logging_deactivation(mlflow_tracking_uri):
    metric_ds = MlflowMetricHistoryDataSet(key="inactive_metric")
    metric_ds._logging_activated = False
    with mlflow.start_run():
        metric_ds.save([0.1])
        assert metric_ds._exists() is False
