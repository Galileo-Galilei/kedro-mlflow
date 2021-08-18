from typing import Dict, List, Optional, Union

import mlflow
import pytest
from kedro.io import DataSetError
from mlflow.tracking import MlflowClient
from pytest_lazyfixture import lazy_fixture

from kedro_mlflow.io.metrics import MlflowMetricsDataSet


def assert_are_metrics_logged(
    data: Dict[str, Union[float, List[float]]],
    client: MlflowClient,
    run_id: str,
    prefix: Optional[str] = None,
) -> bool:
    """Helper function which checks if given metrics where logged.

    Args:
        data: (Dict[str, Union[float, List[float]]]): Logged metrics.
        client: (MlflowClient): MLflow client instance.
        run_id: (str): id of run where data was logged.
        prefix: (Optional[str])
    """
    for key in data.keys():
        metric_key = f"{prefix}.{key}" if prefix else key
        metric = client.get_metric_history(run_id, metric_key)
        data_len = len(data[key]) if isinstance(data[key], list) else 1
        assert len(metric) == data_len
        for idx, item in enumerate(metric):
            data_value = (
                data[key][idx]["value"]
                if isinstance(data[key], list)
                else data[key]["value"]
            )
            assert item.value == data_value and item.key == metric_key
    assert True


@pytest.fixture
def tracking_uri(tmp_path):
    return tmp_path / "mlruns"


@pytest.fixture
def metrics():
    return {
        "metric1": {"step": 0, "value": 1.1},
        "metric2": {"step": 0, "value": 1.2},
    }


@pytest.fixture
def metrics2():
    return {
        "metric1": [
            {"step": 0, "value": 1.1},
            {"step": 1, "value": 1.2},
            {"step": 2, "value": 1.3},
        ],
        "metric2": {"step": 0, "value": 1.2},
        "metric3": {"step": 0, "value": 1.4},
    }


@pytest.fixture
def metrics3():
    return {"metric1": {"step": 0, "value": 1.1}}


@pytest.mark.parametrize(
    "data, prefix",
    [
        (lazy_fixture("metrics"), None),
        (lazy_fixture("metrics"), "test"),
        (lazy_fixture("metrics2"), None),
        (lazy_fixture("metrics2"), "test"),
        (lazy_fixture("metrics3"), None),
        (lazy_fixture("metrics3"), "test"),
    ],
)
def test_mlflow_metrics_dataset_saved_and_logged(tmp_path, tracking_uri, data, prefix):
    """Check if MlflowMetricsDataSet can be saved in catalog when filepath is given,
    and if logged in mlflow.
    """
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix=prefix)

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow_metrics_dataset.save(data)

        # Check if metrics where logged corectly in MLflow.
        assert_are_metrics_logged(data, mlflow_client, run_id, prefix)

    # Check if metrics are stored in catalog.
    catalog_metrics = MlflowMetricsDataSet(
        prefix=prefix,
        # Run id needs to be provided as there is no active run.
        run_id=run_id,
    ).load()

    assert len(catalog_metrics) == len(data)
    for k in catalog_metrics.keys():
        data_key = k.split(".")[-1] if prefix is not None else k
        assert data[data_key] == catalog_metrics[k]


def test_mlflow_metrics_dataset_saved_without_run_id(tmp_path, tracking_uri, metrics3):
    """Check if MlflowMetricsDataSet can be saved in catalog when filepath is given,
    and if logged in mlflow.
    """
    prefix = "test_metric"

    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix=prefix)

    # a mlflow run_id is automatically created
    mlflow_metrics_dataset.save(metrics3)
    run_id = mlflow.active_run().info.run_id

    assert_are_metrics_logged(metrics3, mlflow_client, run_id, prefix)


def test_mlflow_metrics_dataset_exists(tmp_path, tracking_uri, metrics3):
    """Check if MlflowMetricsDataSet is well identified as
    existing if it has already been saved.
    """
    prefix = "test_metric"

    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix=prefix)

    # a mlflow run_id is automatically created
    mlflow_metrics_dataset.save(metrics3)
    assert mlflow_metrics_dataset.exists()


def test_mlflow_metrics_dataset_does_not_exist(tmp_path, tracking_uri, metrics3):
    """Check if MlflowMetricsDataSet is well identified as
    not existingif it has never been saved.
    """

    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow.start_run()  # starts a run toenable mlflow_metrics_dataset to know where to seacrh
    run_id = mlflow.active_run().info.run_id
    mlflow.end_run()
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix="test_metric", run_id=run_id)
    # a mlflow run_id is automatically created
    assert not mlflow_metrics_dataset.exists()


def test_mlflow_metrics_dataset_fails_with_invalid_metric(
    tmp_path, tracking_uri, metrics3
):
    """Check if MlflowMetricsDataSet is well identified as
    not existingif it has never been saved.
    """

    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix="test_metric")

    with pytest.raises(
        DataSetError, match="Unexpected metric value. Should be of type"
    ):
        mlflow_metrics_dataset.save(
            {"metric1": 1}
        )  # key: value is not valid, you must specify {key: {value, step}}


def test_mlflow_metrics_logging_deactivation(tracking_uri, metrics):
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix="hello")

    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())

    mlflow_metrics_dataset._logging_activated = False

    all_runs_id_beginning = set(
        [
            run.run_id
            for k in range(len(mlflow_client.list_experiments()))
            for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
        ]
    )

    mlflow_metrics_dataset.save(metrics)

    all_runs_id_end = set(
        [
            run.run_id
            for k in range(len(mlflow_client.list_experiments()))
            for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
        ]
    )

    assert all_runs_id_beginning == all_runs_id_end


def test_mlflow_metrics_logging_deactivation_is_bool():
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix="hello")

    with pytest.raises(ValueError, match="_logging_activated must be a boolean"):
        mlflow_metrics_dataset._logging_activated = "hello"
